import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Result } from "../../infra/bases/result";
import type { IModuleSurface, SurfacePromptInput } from "../../infra/bases/surface";
import { surfaceCapabilitiesFromConfigs } from "../../infra/helpers/surface_capabilities";
import { resolveModuleSurfaceDirectory, SurfaceLoader } from "../../infra/helpers/surface_loader";
import { modelsRegistryCapabilityConfig } from "./capabilities/registry/registry.service";

const moduleDirectory = dirname(fileURLToPath(import.meta.url));

export function createModelsSurface(): IModuleSurface {
  const loader = new SurfaceLoader(resolveModuleSurfaceDirectory("models", moduleDirectory));

  return {
    moduleId: "models",
    capabilities: async () =>
      Result.ok(surfaceCapabilitiesFromConfigs([modelsRegistryCapabilityConfig])),
    knowledge: () => loader.knowledge(),
    loop: () => loader.loop(),
    prompt: (input?: SurfacePromptInput) => loader.prompt(input),
    skill: () => loader.skill(),
  };
}
