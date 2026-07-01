import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Result } from "../../infra/bases/result";
import type { IModuleSurface, SurfacePromptInput } from "../../infra/bases/surface";
import { surfaceCapabilitiesFromConfigs } from "../../infra/helpers/surface_capabilities";
import { resolveModuleSurfaceDirectory, SurfaceLoader } from "../../infra/helpers/surface_loader";
import { contextProjectsCapabilityConfig } from "./capabilities/projects/projects.service";
import { contextSessionsCapabilityConfig } from "./capabilities/sessions/sessions.service";

const moduleDirectory = dirname(fileURLToPath(import.meta.url));

export function createContextSurface(): IModuleSurface {
  const loader = new SurfaceLoader(resolveModuleSurfaceDirectory("context", moduleDirectory));

  return {
    moduleId: "context",
    capabilities: async () =>
      Result.ok(
        surfaceCapabilitiesFromConfigs([
          contextProjectsCapabilityConfig,
          contextSessionsCapabilityConfig,
        ]),
      ),
    knowledge: () => loader.knowledge(),
    loop: () => loader.loop(),
    prompt: (input?: SurfacePromptInput) => loader.prompt(input),
    skill: () => loader.skill(),
  };
}
