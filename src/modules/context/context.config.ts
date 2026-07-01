import { defineModuleConfig } from "../../infra/bases/module";
import { contextProjectsCapabilityConfig } from "./capabilities/projects/projects.service";
import { contextSessionsCapabilityConfig } from "./capabilities/sessions/sessions.service";

export const contextModuleConfig = defineModuleConfig({
  id: "context",
  name: "Context",
  description: "Agent DevKit projects, sessions and durable context foundations.",
  capabilities: [contextProjectsCapabilityConfig.id, contextSessionsCapabilityConfig.id],
  tests: {
    include: [
      "src/modules/context/context.surface.test.ts",
      "src/modules/context/capabilities/**/*.test.ts",
    ],
  },
} as const);
