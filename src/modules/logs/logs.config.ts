import { defineModuleConfig } from "../../infra/bases/module";
import { logsAnalysisCapabilityConfig } from "./capabilities/analysis/analysis.service";

export const logsModuleConfig = defineModuleConfig({
  id: "logs",
  name: "Logs",
  description: "Agent DevKit usage log analysis and inspection.",
  capabilities: [logsAnalysisCapabilityConfig.id],
  tests: {
    include: [
      "src/modules/logs/logs.surface.test.ts",
      "src/modules/logs/capabilities/**/*.test.ts",
    ],
  },
} as const);
