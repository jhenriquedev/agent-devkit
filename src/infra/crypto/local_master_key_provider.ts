import { randomBytes } from "node:crypto";
import { chmod, mkdir, readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import type { SecretKeyProvider } from "../bases/crypto";
import type { Logger } from "../bases/logger";
import { NullLogger } from "../bases/logger";
import { errorCause } from "../helpers/error_cause";

export type LocalMasterKeyProviderOptions = {
  logger?: Logger;
  stateDirectory?: string;
};

function defaultStateDirectory(): string {
  return join(homedir(), ".agent-devkit");
}

export class LocalMasterKeyProvider implements SecretKeyProvider {
  readonly #legacyKeyPaths: string[];
  readonly #keyPath: string;
  readonly #logger: Logger;

  constructor(options: LocalMasterKeyProviderOptions = {}) {
    const stateDirectory = options.stateDirectory ?? defaultStateDirectory();
    this.#keyPath = join(stateDirectory, "keys", "master.key");
    this.#legacyKeyPaths = [
      join(stateDirectory, "keys", "local.key"),
      join(stateDirectory, "secrets", "master.key"),
      join(stateDirectory, "master.key"),
    ];
    this.#logger = options.logger ?? new NullLogger();
  }

  keyId(): string {
    return "local";
  }

  async getKey(): Promise<Buffer> {
    try {
      return Buffer.from((await readFile(this.#keyPath, "utf8")).trim(), "base64");
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
        this.#logger.write("error", "Local master key read failed.", {
          error: errorCause(error),
          path: this.#keyPath,
        });
        throw error;
      }
    }

    const legacyKey = await this.#readLegacyKey();

    if (legacyKey !== undefined) {
      return this.#persistKey(legacyKey);
    }

    const key = randomBytes(32);
    return this.#persistKey(key);
  }

  async #persistKey(key: Buffer): Promise<Buffer> {
    await mkdir(dirname(this.#keyPath), { recursive: true, mode: 0o700 });

    try {
      await writeFile(this.#keyPath, `${key.toString("base64")}\n`, { flag: "wx", mode: 0o600 });
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "EEXIST") {
        return Buffer.from((await readFile(this.#keyPath, "utf8")).trim(), "base64");
      }

      this.#logger.write("error", "Local master key creation failed.", {
        error: errorCause(error),
        path: this.#keyPath,
      });
      throw error;
    }

    if (process.platform !== "win32") {
      await chmod(dirname(this.#keyPath), 0o700);
      await chmod(this.#keyPath, 0o600);
    }

    return key;
  }

  async #readLegacyKey(): Promise<Buffer | undefined> {
    for (const path of this.#legacyKeyPaths) {
      try {
        return Buffer.from((await readFile(path, "utf8")).trim(), "base64");
      } catch (error) {
        if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
          this.#logger.write("error", "Legacy local master key read failed.", {
            error: errorCause(error),
            path,
          });
          throw error;
        }
      }
    }

    return undefined;
  }
}
