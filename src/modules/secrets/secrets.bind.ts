import { defineModuleBinding, ModuleBinder, type ModuleBinding } from "../../infra/bases/bind";
import type { AgentDevKitErrorCode } from "../../infra/bases/errors";
import type { Result } from "../../infra/bases/result";
import { EncryptedSecretStore } from "../../infra/crypto/encrypted_secret_store";
import { LocalMasterKeyProvider } from "../../infra/crypto/local_master_key_provider";
import { LocalSecretCrypto } from "../../infra/crypto/local_secret_crypto";
import {
  SecretsVaultRepository,
  type SecretsVaultRepositoryPort,
} from "./capabilities/vault/vault.repository";
import { SecretsVaultService } from "./capabilities/vault/vault.service";
import { secretsModuleConfig } from "./secrets.config";

export type SecretsModuleBindOptions = {
  homeDirectory?: string;
  stateDirectory?: string;
};

export type SecretsModuleCapabilities = {
  vault: SecretsVaultService;
};

export type SecretsModuleBinding = ModuleBinding<
  typeof secretsModuleConfig,
  SecretsModuleCapabilities
>;

type SecretsModuleBinderDependencies = {
  vaultRepository: (options: SecretsModuleBindOptions) => SecretsVaultRepositoryPort;
};

function stateDirectory(options: SecretsModuleBindOptions): string | undefined {
  return (
    options.stateDirectory ??
    (options.homeDirectory ? `${options.homeDirectory}/.agent-devkit` : undefined)
  );
}

const defaultDependencies: SecretsModuleBinderDependencies = {
  vaultRepository: (options) => {
    const resolvedStateDirectory = stateDirectory(options);
    const keyProvider = new LocalMasterKeyProvider({ stateDirectory: resolvedStateDirectory });

    return new SecretsVaultRepository({
      store: new EncryptedSecretStore({
        crypto: new LocalSecretCrypto({ keyProvider }),
        stateDirectory: resolvedStateDirectory,
      }),
    });
  },
};

export class SecretsModuleBinder extends ModuleBinder<
  SecretsModuleBindOptions,
  typeof secretsModuleConfig,
  SecretsModuleCapabilities
> {
  readonly #dependencies: SecretsModuleBinderDependencies;

  constructor(dependencies: SecretsModuleBinderDependencies = defaultDependencies) {
    super();
    this.#dependencies = dependencies;
  }

  override bind(
    options: SecretsModuleBindOptions = {},
  ): Result<AgentDevKitErrorCode, SecretsModuleBinding> {
    return defineModuleBinding({
      config: secretsModuleConfig,
      capabilities: {
        vault: new SecretsVaultService({
          repository: this.#dependencies.vaultRepository(options),
        }),
      },
    });
  }
}

export function createSecretsModuleBindings(
  options: SecretsModuleBindOptions = {},
): Result<AgentDevKitErrorCode, SecretsModuleBinding> {
  return new SecretsModuleBinder().bind(options);
}
