import { randomBytes } from "node:crypto";
import { existsSync } from "node:fs";
import { chmod, mkdir, readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import type { SecretKeyProvider } from "../bases/crypto";

export type LocalMasterKeyProviderOptions = {
  stateDirectory?: string;
};

function defaultStateDirectory(): string {
  return join(homedir(), ".agent-devkit");
}

export class LocalMasterKeyProvider implements SecretKeyProvider {
  readonly #keyPath: string;

  constructor(options: LocalMasterKeyProviderOptions = {}) {
    this.#keyPath = join(options.stateDirectory ?? defaultStateDirectory(), "keys", "local.key");
  }

  keyId(): string {
    return "local";
  }

  async getKey(): Promise<Buffer> {
    if (existsSync(this.#keyPath)) {
      return Buffer.from((await readFile(this.#keyPath, "utf8")).trim(), "base64");
    }

    const key = randomBytes(32);
    await mkdir(dirname(this.#keyPath), { recursive: true, mode: 0o700 });
    await writeFile(this.#keyPath, `${key.toString("base64")}\n`, { mode: 0o600 });

    if (process.platform !== "win32") {
      await chmod(dirname(this.#keyPath), 0o700);
      await chmod(this.#keyPath, 0o600);
    }

    return key;
  }
}
