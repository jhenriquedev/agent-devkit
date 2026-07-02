import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Result } from "../../infra/bases/result";
import type { IModuleSurface, SurfacePromptInput } from "../../infra/bases/surface";
import { surfaceCapabilitiesFromConfigs } from "../../infra/helpers/surface_capabilities";
import { resolveModuleSurfaceDirectory, SurfaceLoader } from "../../infra/helpers/surface_loader";
import { logsAnalysisCapabilityConfig } from "./capabilities/analysis/analysis.service";

const moduleDirectory = dirname(fileURLToPath(import.meta.url));

export function createLogsSurface(): IModuleSurface {
  const loader = new SurfaceLoader(resolveModuleSurfaceDirectory("logs", moduleDirectory));

  return {
    moduleId: "logs",
    capabilities: async () =>
      Result.ok(surfaceCapabilitiesFromConfigs([logsAnalysisCapabilityConfig])),
    knowledge: () => loader.knowledge(),
    loop: () => loader.loop(),
    prompt: (input?: SurfacePromptInput) => loader.prompt(input),
    skill: () => loader.skill(),
  };
}
