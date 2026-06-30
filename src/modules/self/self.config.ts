import { defineModuleConfig } from "../../infra/bases/module";
import { updateCapabilityConfig } from "./capabilities/update/update.service";

export const selfModuleConfig = defineModuleConfig({
  id: "self",
  name: "Self",
  description: "Agent DevKit package maintenance capabilities.",
  capabilities: [updateCapabilityConfig.id],
  tests: {
    include: [
      "src/modules/self/self.surface.test.ts",
      "src/modules/self/capabilities/**/*.test.ts",
    ],
  },
} as const);
