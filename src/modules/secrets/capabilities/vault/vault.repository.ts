import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import type { AgentDevKitErrorCode } from "../../../../infra/bases/errors";
import type { Result } from "../../../../infra/bases/result";
import type {
  EncryptedSecretStore,
  SecretAuditEntry,
  SecretSummary,
} from "../../../../infra/crypto/encrypted_secret_store";

export interface SecretsVaultRepositoryPort extends CapabilityRepositoryPort {
  audit(name?: string): Promise<Result<AgentDevKitErrorCode, SecretAuditEntry[]>>;
  get(name: string): Promise<Result<AgentDevKitErrorCode, string>>;
  list(): Promise<Result<AgentDevKitErrorCode, SecretSummary[]>>;
  path(): string;
  reveal(name: string): Promise<Result<AgentDevKitErrorCode, string>>;
  remove(name: string): Promise<Result<AgentDevKitErrorCode, { removed: boolean }>>;
  rotate(
    name: string,
    value: string,
    metadata?: { service?: string },
  ): Promise<Result<AgentDevKitErrorCode, SecretSummary>>;
  set(
    name: string,
    value: string,
    metadata?: { service?: string },
  ): Promise<Result<AgentDevKitErrorCode, SecretSummary>>;
}

export type SecretsVaultRepositoryOptions = {
  store: EncryptedSecretStore;
};

export class SecretsVaultRepository implements SecretsVaultRepositoryPort {
  readonly repositoryId = "secrets.vault.repository";
  readonly #store: EncryptedSecretStore;

  constructor(options: SecretsVaultRepositoryOptions) {
    this.#store = options.store;
  }

  audit(name?: string): Promise<Result<AgentDevKitErrorCode, SecretAuditEntry[]>> {
    return this.#store.audit(name);
  }

  get(name: string): Promise<Result<AgentDevKitErrorCode, string>> {
    return this.#store.get(name);
  }

  list(): Promise<Result<AgentDevKitErrorCode, SecretSummary[]>> {
    return this.#store.list();
  }

  path(): string {
    return this.#store.path();
  }

  remove(name: string): Promise<Result<AgentDevKitErrorCode, { removed: boolean }>> {
    return this.#store.remove(name);
  }

  reveal(name: string): Promise<Result<AgentDevKitErrorCode, string>> {
    return this.#store.reveal(name);
  }

  rotate(
    name: string,
    value: string,
    metadata: { service?: string } = {},
  ): Promise<Result<AgentDevKitErrorCode, SecretSummary>> {
    return this.#store.rotate(name, value, metadata);
  }

  set(
    name: string,
    value: string,
    metadata: { service?: string } = {},
  ): Promise<Result<AgentDevKitErrorCode, SecretSummary>> {
    return this.#store.set(name, value, metadata);
  }
}
