import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Result } from "../../infra/bases/result";
import type { IModuleSurface, SurfacePromptInput } from "../../infra/bases/surface";
import { surfaceCapabilitiesFromConfigs } from "../../infra/helpers/surface_capabilities";
import { resolveModuleSurfaceDirectory, SurfaceLoader } from "../../infra/helpers/surface_loader";
import { personalizationCapabilityConfig } from "./capabilities/personalization/personalization.service";
import { preferencesCapabilityConfig } from "./capabilities/preferences/preferences.service";

const moduleDirectory = dirname(fileURLToPath(import.meta.url));

export function createUserSurface(): IModuleSurface {
  const loader = new SurfaceLoader(resolveModuleSurfaceDirectory("user", moduleDirectory));

  return {
    moduleId: "user",
    capabilities: async () =>
      Result.ok(
        surfaceCapabilitiesFromConfigs([
          personalizationCapabilityConfig,
          preferencesCapabilityConfig,
        ]),
      ),
    knowledge: () => loader.knowledge(),
    loop: () => loader.loop(),
    prompt: (input?: SurfacePromptInput) => loader.prompt(input),
    skill: () => loader.skill(),
  };
}
