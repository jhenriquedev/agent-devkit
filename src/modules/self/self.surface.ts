import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Result } from "../../infra/bases/result";
import type { IModuleSurface, SurfacePromptInput } from "../../infra/bases/surface";
import { surfaceCapabilitiesFromConfigs } from "../../infra/helpers/surface_capabilities";
import { resolveModuleSurfaceDirectory, SurfaceLoader } from "../../infra/helpers/surface_loader";
import { updateCapabilityConfig } from "./capabilities/update/update.service";

const moduleDirectory = dirname(fileURLToPath(import.meta.url));

export function createSelfSurface(): IModuleSurface {
  const loader = new SurfaceLoader(resolveModuleSurfaceDirectory("self", moduleDirectory));

  return {
    moduleId: "self",
    capabilities: async () => Result.ok(surfaceCapabilitiesFromConfigs([updateCapabilityConfig])),
    knowledge: () => loader.knowledge(),
    loop: () => loader.loop(),
    prompt: (input?: SurfacePromptInput) => loader.prompt(input),
    skill: () => loader.skill(),
  };
}
