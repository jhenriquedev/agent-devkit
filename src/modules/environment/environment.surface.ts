import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Result } from "../../infra/bases/result";
import type { IModuleSurface, SurfacePromptInput } from "../../infra/bases/surface";
import { surfaceCapabilitiesFromConfigs } from "../../infra/helpers/surface_capabilities";
import { resolveModuleSurfaceDirectory, SurfaceLoader } from "../../infra/helpers/surface_loader";
import { dependenciesCapabilityConfig } from "./capabilities/dependencies/dependencies.service";

const moduleDirectory = dirname(fileURLToPath(import.meta.url));

export function createEnvironmentSurface(): IModuleSurface {
  const loader = new SurfaceLoader(resolveModuleSurfaceDirectory("environment", moduleDirectory));

  return {
    moduleId: "environment",
    capabilities: async () =>
      Result.ok(surfaceCapabilitiesFromConfigs([dependenciesCapabilityConfig])),
    knowledge: () => loader.knowledge(),
    loop: () => loader.loop(),
    prompt: (input?: SurfacePromptInput) => loader.prompt(input),
    skill: () => loader.skill(),
  };
}
