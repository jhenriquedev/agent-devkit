import { defineModuleConfig } from "../../infra/bases/module";
import { secretsVaultCapabilityConfig } from "./capabilities/vault/vault.service";

export const secretsModuleConfig = defineModuleConfig({
  id: "secrets",
  name: "Secrets",
  description: "Encrypted local credential storage for external service configuration.",
  capabilities: [secretsVaultCapabilityConfig.id],
  tests: {
    include: [
      "src/modules/secrets/secrets.surface.test.ts",
      "src/modules/secrets/capabilities/**/*.test.ts",
    ],
  },
} as const);
