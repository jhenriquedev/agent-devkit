import { randomBytes } from "node:crypto";
import {
  access,
  appendFile,
  mkdir,
  readdir,
  readFile,
  rename,
  rm,
  writeFile,
} from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, isAbsolute, join, resolve, sep } from "node:path";
import type {
  AgentDataEntry,
  AgentDataPath,
  AgentDataStore,
  AgentDataWriteOptions,
} from "../bases/data_store";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";

export type LocalAgentDataStoreOptions = {
  rootDirectory?: string;
};

function defaultRootDirectory(): string {
  return join(homedir(), ".agent-devkit", "data");
}

function hasPathSeparator(segment: string): boolean {
  return segment.includes("/") || segment.includes("\\");
}

function isNotFoundError(error: unknown): boolean {
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    (error as { code?: unknown }).code === "ENOENT"
  );
}

export class LocalAgentDataStore implements AgentDataStore {
  readonly #rootDirectory: string;

  constructor(options: LocalAgentDataStoreOptions = {}) {
    this.#rootDirectory = resolve(options.rootDirectory ?? defaultRootDirectory());
  }

  rootDirectory(): string {
    return this.#rootDirectory;
  }

  resolve(path: AgentDataPath): Result<AgentDevKitErrorCode, string> {
    if (
      path.segments.some(
        (segment) =>
          segment.length === 0 ||
          segment === "." ||
          segment === ".." ||
          isAbsolute(segment) ||
          hasPathSeparator(segment),
      )
    ) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const target = resolve(this.#rootDirectory, path.namespace, ...path.segments);
    const allowedRoot = `${this.#rootDirectory}${sep}`;

    if (target !== this.#rootDirectory && !target.startsWith(allowedRoot)) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    return Result.ok(target);
  }

  async readJson<T>(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, T>> {
    const content = await this.readText(path);

    if (content.isErr()) {
      return Result.fail(content.unwrapError());
    }

    try {
      return Result.ok(JSON.parse(content.unwrap()) as T);
    } catch {
      return Result.fail(ErrorCodes.InvalidInput);
    }
  }

  async writeJson<T>(
    path: AgentDataPath,
    value: T,
    options: AgentDataWriteOptions = {},
  ): Promise<Result<AgentDevKitErrorCode, void>> {
    return this.writeText(path, `${JSON.stringify(value, null, 2)}\n`, options);
  }

  async appendJsonl<T>(
    path: AgentDataPath,
    value: T,
    _options: AgentDataWriteOptions = {},
  ): Promise<Result<AgentDevKitErrorCode, void>> {
    const target = this.resolve(path);

    if (target.isErr()) {
      return Result.fail(target.unwrapError());
    }

    try {
      await mkdir(dirname(target.unwrap()), { recursive: true });
      await appendFile(target.unwrap(), `${JSON.stringify(value)}\n`, "utf8");
      return Result.ok(undefined);
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }

  async readJsonl<T>(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, T[]>> {
    const content = await this.readText(path);

    if (content.isErr()) {
      return Result.fail(content.unwrapError());
    }

    try {
      return Result.ok(
        content
          .unwrap()
          .split("\n")
          .map((line) => line.trim())
          .filter((line) => line.length > 0)
          .map((line) => JSON.parse(line) as T),
      );
    } catch {
      return Result.fail(ErrorCodes.InvalidInput);
    }
  }

  async readText(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, string>> {
    const target = this.resolve(path);

    if (target.isErr()) {
      return Result.fail(target.unwrapError());
    }

    try {
      return Result.ok(await readFile(target.unwrap(), "utf8"));
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  async writeText(
    path: AgentDataPath,
    value: string,
    options: AgentDataWriteOptions = {},
  ): Promise<Result<AgentDevKitErrorCode, void>> {
    return this.#write(path, value, options);
  }

  async readBinary(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, Uint8Array>> {
    const target = this.resolve(path);

    if (target.isErr()) {
      return Result.fail(target.unwrapError());
    }

    try {
      return Result.ok(await readFile(target.unwrap()));
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  async writeBinary(
    path: AgentDataPath,
    value: Uint8Array,
    options: AgentDataWriteOptions = {},
  ): Promise<Result<AgentDevKitErrorCode, void>> {
    return this.#write(path, value, options);
  }

  async list(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, AgentDataEntry[]>> {
    const target = this.resolve(path);

    if (target.isErr()) {
      return Result.fail(target.unwrapError());
    }

    try {
      const entries = await readdir(target.unwrap(), { withFileTypes: true });
      return Result.ok(
        entries
          .map((entry) => ({
            kind: entry.isDirectory() ? ("directory" as const) : ("file" as const),
            name: entry.name,
            path: { namespace: path.namespace, segments: [...path.segments, entry.name] },
          }))
          .sort((left, right) => left.name.localeCompare(right.name)),
      );
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  async remove(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, void>> {
    const target = this.resolve(path);

    if (target.isErr()) {
      return Result.fail(target.unwrapError());
    }

    try {
      await rm(target.unwrap(), { force: true, recursive: true });
      return Result.ok(undefined);
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }

  async exists(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, boolean>> {
    const target = this.resolve(path);

    if (target.isErr()) {
      return Result.fail(target.unwrapError());
    }

    try {
      await access(target.unwrap());
      return Result.ok(true);
    } catch (error) {
      return isNotFoundError(error) ? Result.ok(false) : Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  async #write(
    path: AgentDataPath,
    value: string | Uint8Array,
    options: AgentDataWriteOptions,
  ): Promise<Result<AgentDevKitErrorCode, void>> {
    const target = this.resolve(path);

    if (target.isErr()) {
      return Result.fail(target.unwrapError());
    }

    const atomic = options.atomic ?? true;

    try {
      await mkdir(dirname(target.unwrap()), { recursive: true });

      if (!atomic) {
        await writeFile(target.unwrap(), value);
        return Result.ok(undefined);
      }

      const tempPath = join(
        dirname(target.unwrap()),
        `.agent-data-${process.pid}-${randomBytes(6).toString("hex")}.tmp`,
      );

      try {
        await writeFile(tempPath, value, { flag: "wx" });
        await rename(tempPath, target.unwrap());
      } catch (error) {
        await rm(tempPath, { force: true }).catch(() => undefined);
        throw error;
      }

      return Result.ok(undefined);
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }
}
