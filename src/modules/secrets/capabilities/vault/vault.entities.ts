import type { SecretSummary } from "../../../../infra/crypto/encrypted_secret_store";

export type SecretView = SecretSummary & {
  value?: string;
};

export type SecretsVaultOptions =
  | { action: "list" }
  | { action: "remove"; name: string }
  | { action: "set"; name: string; service?: string; value: string }
  | { action: "show"; name: string; reveal?: boolean };

export type SecretsVaultResult =
  | {
      action: "list";
      path: string;
      secrets: SecretView[];
    }
  | {
      action: "remove";
      path: string;
      removed: boolean;
      secret: { name: string };
    }
  | {
      action: "set";
      path: string;
      secret: SecretView;
    }
  | {
      action: "show";
      path: string;
      secret: SecretView;
    };
