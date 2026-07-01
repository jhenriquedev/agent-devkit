import { randomBytes } from "node:crypto";
import { access, chmod, mkdir, readFile, rename, unlink, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import type { EncryptedPayload, SecretCrypto } from "../bases/crypto";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import type { Logger } from "../bases/logger";
import { NullLogger } from "../bases/logger";
import { Result } from "../bases/result";
import { errorCause } from "../helpers/error_cause";

export type SecretMetadata = {
  createdAt: string;
  name: string;
  service?: string;
  updatedAt: string;
};

export type SecretAuditAction = "created" | "removed" | "revealed" | "rotated" | "updated";

export type SecretAuditEntry = {
  action: SecretAuditAction;
  name: string;
  service?: string;
  timestamp: string;
};

export type StoredSecret = SecretMetadata & {
  encrypted: EncryptedPayload;
};

export type SecretSummary = SecretMetadata;
export type RevealedSecret = {
  secret: SecretSummary;
  value: string;
};

type VaultFile = {
  audit: SecretAuditEntry[];
  schema: "agent-devkit.secret-vault/v1";
  secrets: StoredSecret[];
};

export type EncryptedSecretStoreOptions = {
  clock?: () => Date;
  crypto: SecretCrypto;
  logger?: Logger;
  stateDirectory?: string;
};

function defaultStateDirectory(): string {
  return join(homedir(), ".agent-devkit");
}

function defaultVault(): VaultFile {
  return {
    audit: [],
    schema: "agent-devkit.secret-vault/v1",
    secrets: [],
  };
}

function sortSecrets(left: SecretSummary, right: SecretSummary): number {
  return left.name.localeCompare(right.name);
}

export class EncryptedSecretStore {
  readonly #clock: () => Date;
  readonly #crypto: SecretCrypto;
  readonly #logger: Logger;
  readonly #vaultPath: string;

  constructor(options: EncryptedSecretStoreOptions) {
    this.#clock = options.clock ?? (() => new Date());
    this.#crypto = options.crypto;
    this.#logger = options.logger ?? new NullLogger();
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

  async reveal(name: string): Promise<Result<AgentDevKitErrorCode, RevealedSecret>> {
    const vault = await this.#readVault();

    if (vault.isErr()) {
      return Result.fail(vault.unwrapError());
    }

    const existing = vault.unwrap();
    const secret = existing.secrets.find((candidate) => candidate.name === name);

    if (secret === undefined) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const value = await this.#crypto.decryptString(secret.encrypted);

    if (value.isErr()) {
      return Result.fail(value.unwrapError());
    }

    const save = await this.#writeVault({
      ...existing,
      audit: [...existing.audit, this.#auditEntry("revealed", secret)],
    });

    return save.isOk()
      ? Result.ok({
          secret: this.#summary(secret),
          value: value.unwrap(),
        })
      : Result.fail(save.unwrapError());
  }

  async list(): Promise<Result<AgentDevKitErrorCode, SecretSummary[]>> {
    const vault = await this.#readVault();

    if (vault.isErr()) {
      return Result.fail(vault.unwrapError());
    }

    return Result.ok(
      vault
        .unwrap()
        .secrets.map((secret) => this.#summary(secret))
        .sort(sortSecrets),
    );
  }

  async audit(name?: string): Promise<Result<AgentDevKitErrorCode, SecretAuditEntry[]>> {
    const vault = await this.#readVault();

    if (vault.isErr()) {
      return Result.fail(vault.unwrapError());
    }

    const events = vault
      .unwrap()
      .audit.filter((entry) => name === undefined || entry.name === name)
      .sort((left, right) => left.timestamp.localeCompare(right.timestamp));

    return Result.ok(events);
  }

  async remove(name: string): Promise<Result<AgentDevKitErrorCode, { removed: boolean }>> {
    const vault = await this.#readVault();

    if (vault.isErr()) {
      return Result.fail(vault.unwrapError());
    }

    const existing = vault.unwrap();
    const removed = existing.secrets.find((secret) => secret.name === name);
    const next: VaultFile = {
      ...existing,
      audit:
        removed === undefined
          ? existing.audit
          : [...existing.audit, this.#auditEntry("removed", removed)],
      secrets: existing.secrets.filter((secret) => secret.name !== name),
    };
    const save = await this.#writeVault(next);

    if (save.isErr()) {
      return Result.fail(save.unwrapError());
    }

    return Result.ok({ removed: next.secrets.length !== existing.secrets.length });
  }

  async rotate(
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

    const existing = vault.unwrap().secrets.find((secret) => secret.name === name);

    if (existing === undefined) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const encrypted = await this.#crypto.encryptString(value);

    if (encrypted.isErr()) {
      return Result.fail(encrypted.unwrapError());
    }

    const now = this.#now();
    const secret: StoredSecret = {
      createdAt: existing.createdAt,
      encrypted: encrypted.unwrap(),
      name,
      service: metadata.service ?? existing.service,
      updatedAt: now,
    };
    const next: VaultFile = {
      schema: "agent-devkit.secret-vault/v1",
      audit: [...vault.unwrap().audit, this.#auditEntry("rotated", secret, now)],
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

    const now = this.#now();
    const existing = vault.unwrap().secrets.find((secret) => secret.name === name);
    const secret: StoredSecret = {
      createdAt: existing?.createdAt ?? now,
      encrypted: encrypted.unwrap(),
      name,
      service: metadata.service ?? existing?.service,
      updatedAt: now,
    };
    const next: VaultFile = {
      schema: "agent-devkit.secret-vault/v1",
      audit: [
        ...vault.unwrap().audit,
        this.#auditEntry(existing === undefined ? "created" : "updated", secret, now),
      ],
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
      const payload = JSON.parse(await readFile(this.#vaultPath, "utf8")) as Partial<VaultFile>;

      if (payload.schema !== "agent-devkit.secret-vault/v1" || !Array.isArray(payload.secrets)) {
        return Result.fail(ErrorCodes.InvalidInput);
      }

      return Result.ok({
        audit: Array.isArray(payload.audit) ? payload.audit : [],
        schema: payload.schema,
        secrets: payload.secrets,
      });
    } catch (error) {
      this.#logger.write("error", "Secret vault read failed.", {
        error: errorCause(error),
        path: this.#vaultPath,
      });
      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  async #writeVault(vault: VaultFile): Promise<Result<AgentDevKitErrorCode, void>> {
    const directory = dirname(this.#vaultPath);
    const tempPath = join(directory, `.vault-${process.pid}-${randomBytes(6).toString("hex")}.tmp`);

    try {
      await mkdir(directory, { recursive: true, mode: 0o700 });
      await writeFile(tempPath, `${JSON.stringify(vault, null, 2)}\n`, {
        flag: "wx",
        mode: 0o600,
      });
      if (process.platform !== "win32") {
        await chmod(tempPath, 0o600);
      }
      await rename(tempPath, this.#vaultPath);
      return Result.ok(undefined);
    } catch (error) {
      await unlink(tempPath).catch(() => undefined);
      this.#logger.write("error", "Secret vault write failed.", {
        error: errorCause(error),
        path: this.#vaultPath,
      });
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }

  #summary(secret: SecretMetadata): SecretSummary {
    return {
      createdAt: secret.createdAt,
      name: secret.name,
      service: secret.service,
      updatedAt: secret.updatedAt,
    };
  }

  #auditEntry(action: SecretAuditAction, secret: SecretMetadata, timestamp = this.#now()) {
    return {
      action,
      name: secret.name,
      service: secret.service,
      timestamp,
    };
  }

  #now(): string {
    return this.#clock().toISOString();
  }
}
