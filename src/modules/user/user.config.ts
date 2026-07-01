import { defineModuleConfig } from "../../infra/bases/module";
import { personalizationCapabilityConfig } from "./capabilities/personalization/personalization.service";
import { preferencesCapabilityConfig } from "./capabilities/preferences/preferences.service";

export const userModuleConfig = defineModuleConfig({
  id: "user",
  name: "User",
  description: "User-level Agent DevKit preferences and personalization.",
  capabilities: [personalizationCapabilityConfig.id, preferencesCapabilityConfig.id],
  tests: {
    include: [
      "src/modules/user/user.surface.test.ts",
      "src/modules/user/capabilities/**/*.test.ts",
    ],
  },
} as const);
