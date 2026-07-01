import { defineModuleConfig } from "../../infra/bases/module";
import { dependenciesCapabilityConfig } from "./capabilities/dependencies/dependencies.service";

export const environmentModuleConfig = defineModuleConfig({
  id: "environment",
  name: "Environment",
  description: "External dependency discovery, planning and runtime environment checks.",
  capabilities: [dependenciesCapabilityConfig.id],
  tests: {
    include: [
      "src/modules/environment/environment.surface.test.ts",
      "src/modules/environment/capabilities/**/*.test.ts",
    ],
  },
} as const);
