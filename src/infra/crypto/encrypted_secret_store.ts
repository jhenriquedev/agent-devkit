import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import type { EncryptedPayload, SecretCrypto } from "../bases/crypto";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";

export type SecretMetadata = {
  createdAt: string;
  name: string;
  service?: string;
  updatedAt: string;
};

export type StoredSecret = SecretMetadata & {
  encrypted: EncryptedPayload;
};

export type SecretSummary = SecretMetadata;

type VaultFile = {
  schema: "agent-devkit.secret-vault/v1";
  secrets: StoredSecret[];
};

export type EncryptedSecretStoreOptions = {
  crypto: SecretCrypto;
  stateDirectory?: string;
};

function defaultStateDirectory(): string {
  return join(homedir(), ".agent-devkit");
}

function defaultVault(): VaultFile {
  return {
    schema: "agent-devkit.secret-vault/v1",
    secrets: [],
  };
}

export class EncryptedSecretStore {
  readonly #crypto: SecretCrypto;
  readonly #vaultPath: string;

  constructor(options: EncryptedSecretStoreOptions) {
    this.#crypto = options.crypto;
    this.#vaultPath = join(
      options.stateDirectory ?? defaultStateDirectory(),
      "secrets",
      "vault.json",
    );
  }

  path(): string {
    return this.#vaultPath;
  }

  async get(name: string): Promise<Result<AgentDevKitErrorCode, string>> {
    const vault = await this.#readVault();

    if (vault.isErr()) {
      return Result.fail(vault.unwrapError());
    }

    const secret = vault.unwrap().secrets.find((candidate) => candidate.name === name);

    if (secret === undefined) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    return this.#crypto.decryptString(secret.encrypted);
  }

  async list(): Promise<Result<AgentDevKitErrorCode, SecretSummary[]>> {
    const vault = await this.#readVault();

    if (vault.isErr()) {
      return Result.fail(vault.unwrapError());
    }

    return Result.ok(
      vault
        .unwrap()
        .secrets.map(({ createdAt, name, service, updatedAt }) => ({
          createdAt,
          name,
          service,
          updatedAt,
        }))
        .sort((left, right) => left.name.localeCompare(right.name)),
    );
  }

  async remove(name: string): Promise<Result<AgentDevKitErrorCode, { removed: boolean }>> {
    const vault = await this.#readVault();

    if (vault.isErr()) {
      return Result.fail(vault.unwrapError());
    }

    const existing = vault.unwrap();
    const next: VaultFile = {
      ...existing,
      secrets: existing.secrets.filter((secret) => secret.name !== name),
    };
    const save = await this.#writeVault(next);

    if (save.isErr()) {
      return Result.fail(save.unwrapError());
    }

    return Result.ok({ removed: next.secrets.length !== existing.secrets.length });
  }

  async set(
    name: string,
    value: string,
    metadata: { service?: string } = {},
  ): Promise<Result<AgentDevKitErrorCode, SecretSummary>> {
    if (name.trim().length === 0 || value.length === 0) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const vault = await this.#readVault();

    if (vault.isErr()) {
      return Result.fail(vault.unwrapError());
    }

    const encrypted = await this.#crypto.encryptString(value);

    if (encrypted.isErr()) {
      return Result.fail(encrypted.unwrapError());
    }

    const now = new Date().toISOString();
    const existing = vault.unwrap().secrets.find((secret) => secret.name === name);
    const secret: StoredSecret = {
      createdAt: existing?.createdAt ?? now,
      encrypted: encrypted.unwrap(),
      name,
      service: metadata.service,
      updatedAt: now,
    };
    const next: VaultFile = {
      schema: "agent-devkit.secret-vault/v1",
      secrets: [...vault.unwrap().secrets.filter((candidate) => candidate.name !== name), secret],
    };
    const save = await this.#writeVault(next);

    if (save.isErr()) {
      return Result.fail(save.unwrapError());
    }

    return Result.ok({
      createdAt: secret.createdAt,
      name: secret.name,
      service: secret.service,
      updatedAt: secret.updatedAt,
    });
  }

  async #readVault(): Promise<Result<AgentDevKitErrorCode, VaultFile>> {
    try {
      await access(this.#vaultPath);
    } catch {
      return Result.ok(defaultVault());
    }

    try {
      const payload = JSON.parse(await readFile(this.#vaultPath, "utf8")) as VaultFile;

      if (payload.schema !== "agent-devkit.secret-vault/v1" || !Array.isArray(payload.secrets)) {
        return Result.fail(ErrorCodes.InvalidInput);
      }

      return Result.ok(payload);
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  async #writeVault(vault: VaultFile): Promise<Result<AgentDevKitErrorCode, void>> {
    try {
      await mkdir(dirname(this.#vaultPath), { recursive: true, mode: 0o700 });
      await writeFile(this.#vaultPath, `${JSON.stringify(vault, null, 2)}\n`, { mode: 0o600 });
      return Result.ok(undefined);
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }
}
