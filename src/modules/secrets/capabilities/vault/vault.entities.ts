import type {
  SecretAuditEntry,
  SecretSummary,
} from "../../../../infra/crypto/encrypted_secret_store";

export type SecretView = SecretSummary & {
  value?: string;
};

export type SecretsVaultOptions =
  | { action: "audit"; name?: string }
  | { action: "list" }
  | { action: "remove"; name: string }
  | { action: "rotate"; name: string; service?: string; value: string }
  | { action: "set"; name: string; service?: string; value: string }
  | { action: "show"; name: string; reveal?: boolean };

export type SecretsVaultResult =
  | {
      action: "audit";
      events: SecretAuditEntry[];
      path: string;
    }
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
      action: "rotate";
      path: string;
      secret: SecretView;
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
