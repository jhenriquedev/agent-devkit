import { defineModuleConfig } from "../../infra/bases/module";
import { modelsRegistryCapabilityConfig } from "./capabilities/registry/registry.service";

export const modelsModuleConfig = defineModuleConfig({
  id: "models",
  name: "Models",
  description: "Local LLM model catalog and lifecycle: list, install, update, remove and select.",
  capabilities: [modelsRegistryCapabilityConfig.id],
  tests: {
    include: [
      "src/modules/models/models.surface.test.ts",
      "src/modules/models/capabilities/**/*.test.ts",
    ],
  },
} as const);
