import { defineModuleConfig } from "../../infra/bases/module";
import { doctorCapabilityConfig } from "./capabilities/doctor/doctor.service";
import { initCapabilityConfig } from "./capabilities/init/init.service";
import { resetCapabilityConfig } from "./capabilities/reset/reset.service";

export const projectModuleConfig = defineModuleConfig({
  id: "project",
  name: "Project",
  description: "Project-local Agent DevKit state, diagnostics and maintenance.",
  capabilities: [doctorCapabilityConfig.id, initCapabilityConfig.id, resetCapabilityConfig.id],
  tests: {
    include: [
      "src/modules/project/project.surface.test.ts",
      "src/modules/project/capabilities/**/*.test.ts",
    ],
  },
} as const);
