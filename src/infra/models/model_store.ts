import { createHash } from "node:crypto";
import { once } from "node:events";
import { createReadStream, createWriteStream } from "node:fs";
import { access, mkdir, readdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { basename, join } from "node:path";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { type InstalledModel, InstalledModelSchema, type ModelCatalogEntry } from "../bases/model";
import { Result } from "../bases/result";

export type ModelDownloadProgress = {
  downloadedBytes: number;
  totalBytes: number;
};

export type ModelStoreOptions = {
  clock?: () => Date;
  downloadTimeoutMs?: number;
  stateDirectory?: string;
};

function defaultStateDirectory(): string {
  return join(homedir(), ".agent-devkit");
}

function errno(error: unknown): string | undefined {
  return typeof (error as NodeJS.ErrnoException).code === "string"
    ? (error as NodeJS.ErrnoException).code
    : undefined;
}

export class ModelStore {
  readonly #clock: () => Date;
  readonly #directory: string;
  readonly #downloadTimeoutMs: number;

  constructor(options: ModelStoreOptions = {}) {
    this.#clock = options.clock ?? (() => new Date());
    this.#directory = join(options.stateDirectory ?? defaultStateDirectory(), "models");
    this.#downloadTimeoutMs = options.downloadTimeoutMs ?? 10 * 60 * 1000;
  }

  directory(): string {
    return this.#directory;
  }

  async status(id: string): Promise<Result<AgentDevKitErrorCode, InstalledModel | undefined>> {
    let raw: string;

    try {
      raw = await readFile(this.#metadataPath(id), "utf8");
    } catch (error) {
      return errno(error) === "ENOENT"
        ? Result.ok(undefined)
        : Result.fail(ErrorCodes.FileReadFailed);
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return Result.ok(undefined);
    }

    const model = InstalledModelSchema.safeParse(parsed);

    if (!model.success) {
      return Result.ok(undefined);
    }

    try {
      await access(this.#modelPath(id));
    } catch {
      return Result.ok(undefined);
    }

    return Result.ok(model.data);
  }

  async list(): Promise<Result<AgentDevKitErrorCode, InstalledModel[]>> {
    const ids = await this.installedIds();

    if (ids.isErr()) {
      return Result.fail(ids.unwrapError());
    }

    const installed: InstalledModel[] = [];

    for (const id of ids.unwrap()) {
      const status = await this.status(id);
      const model = status.isOk() ? status.unwrap() : undefined;

      if (model !== undefined) {
        installed.push(model);
      }
    }

    return Result.ok(installed);
  }

  async installedIds(): Promise<Result<AgentDevKitErrorCode, string[]>> {
    let files: string[];

    try {
      files = await readdir(this.#directory);
    } catch (error) {
      return errno(error) === "ENOENT" ? Result.ok([]) : Result.fail(ErrorCodes.FileReadFailed);
    }

    return Result.ok(
      files
        .filter((file) => file.endsWith(".gguf"))
        .map((file) => basename(file, ".gguf"))
        .sort(),
    );
  }

  async install(
    entry: ModelCatalogEntry,
    options: { onProgress?: (progress: ModelDownloadProgress) => void } = {},
  ): Promise<Result<AgentDevKitErrorCode, InstalledModel>> {
    const target = this.#modelPath(entry.id);
    const temp = `${target}.part`;
    const hash = createHash("sha256");
    const abortController = new AbortController();
    const timeout = setTimeout(() => abortController.abort(), this.#downloadTimeoutMs);

    try {
      await mkdir(this.#directory, { recursive: true, mode: 0o700 });

      const response = await fetch(entry.url, { signal: abortController.signal });

      if (!response.ok || response.body === null) {
        return Result.fail(ErrorCodes.NetworkRequestFailed);
      }

      const writeStream = createWriteStream(temp, { mode: 0o600 });
      const reader = response.body.getReader();
      let downloadedBytes = 0;

      try {
        for (;;) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          if (value === undefined) {
            continue;
          }

          hash.update(value);
          downloadedBytes += value.byteLength;
          options.onProgress?.({ downloadedBytes, totalBytes: entry.sizeBytes });

          if (!writeStream.write(value)) {
            await once(writeStream, "drain");
          }
        }

        await new Promise<void>((resolve, reject) => {
          writeStream.on("error", reject);
          writeStream.end(() => resolve());
        });
      } finally {
        reader.releaseLock();
      }

      const digest = hash.digest("hex");

      if (entry.sha256 !== undefined && digest.toLowerCase() !== entry.sha256.toLowerCase()) {
        await rm(temp, { force: true }).catch(() => undefined);
        return Result.fail(ErrorCodes.ModelVerificationFailed);
      }

      await rename(temp, target);

      const installed: InstalledModel = {
        id: entry.id,
        path: target,
        sizeBytes: downloadedBytes,
        sha256: digest,
        installedAt: this.#clock().toISOString(),
      };

      await writeFile(this.#metadataPath(entry.id), `${JSON.stringify(installed, null, 2)}\n`, {
        mode: 0o600,
      });

      return Result.ok(installed);
    } catch (error) {
      await rm(temp, { force: true }).catch(() => undefined);
      return Result.fail(
        errno(error) === undefined ? ErrorCodes.NetworkRequestFailed : ErrorCodes.FileWriteFailed,
      );
    } finally {
      clearTimeout(timeout);
    }
  }

  async uninstall(id: string): Promise<Result<AgentDevKitErrorCode, { removed: boolean }>> {
    try {
      let removed = false;

      for (const path of [this.#modelPath(id), this.#metadataPath(id)]) {
        try {
          await rm(path);
          removed = true;
        } catch (error) {
          if (errno(error) !== "ENOENT") {
            throw error;
          }
        }
      }

      for (const role of [undefined, "agent", "chat"]) {
        const current = await this.#readDefaultFile(this.#defaultPath(role));

        if (current.isOk() && current.unwrap() === id) {
          await rm(this.#defaultPath(role), { force: true }).catch(() => undefined);
        }
      }

      return Result.ok({ removed });
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }

  async verify(
    id: string,
    expectedSha256?: string,
  ): Promise<Result<AgentDevKitErrorCode, boolean>> {
    const status = await this.status(id);

    if (status.isErr()) {
      return Result.fail(status.unwrapError());
    }

    const installed = status.unwrap();

    if (installed === undefined) {
      return Result.fail(ErrorCodes.ModelNotFound);
    }

    const expected = (expectedSha256 ?? installed.sha256)?.toLowerCase();

    if (expected === undefined) {
      return Result.ok(true);
    }

    try {
      const hash = createHash("sha256");

      for await (const chunk of createReadStream(this.#modelPath(id))) {
        hash.update(chunk as Buffer);
      }

      return Result.ok(hash.digest("hex").toLowerCase() === expected);
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  async getDefault(role?: string): Promise<Result<AgentDevKitErrorCode, string | undefined>> {
    const primary = await this.#readDefaultFile(this.#defaultPath(role));

    if (primary.isErr() || primary.unwrap() !== undefined || role === undefined) {
      return primary;
    }

    return this.#readDefaultFile(this.#defaultPath());
  }

  async setDefault(id: string, role?: string): Promise<Result<AgentDevKitErrorCode, void>> {
    const status = await this.status(id);

    if (status.isErr()) {
      return Result.fail(status.unwrapError());
    }

    if (status.unwrap() === undefined) {
      return Result.fail(ErrorCodes.ModelNotFound);
    }

    try {
      await mkdir(this.#directory, { recursive: true, mode: 0o700 });
      await writeFile(this.#defaultPath(role), `${id}\n`, { mode: 0o600 });
      return Result.ok(undefined);
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }

  #modelPath(id: string): string {
    return join(this.#directory, `${id}.gguf`);
  }

  #metadataPath(id: string): string {
    return join(this.#directory, `${id}.json`);
  }

  #defaultPath(role?: string): string {
    return join(this.#directory, role === undefined ? "default" : `default-${role}`);
  }

  async #readDefaultFile(path: string): Promise<Result<AgentDevKitErrorCode, string | undefined>> {
    try {
      const id = (await readFile(path, "utf8")).trim();
      return Result.ok(id.length > 0 ? id : undefined);
    } catch (error) {
      return errno(error) === "ENOENT"
        ? Result.ok(undefined)
        : Result.fail(ErrorCodes.FileReadFailed);
    }
  }
}
