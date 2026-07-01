import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { AgentDevKitErrorCode } from "../../infra/bases/errors";
import type { Result } from "../../infra/bases/result";
import { Result as ResultValue } from "../../infra/bases/result";
import type { IModuleSurface, SurfacePromptInput } from "../../infra/bases/surface";
import { surfaceCapabilitiesFromConfigs } from "../../infra/helpers/surface_capabilities";
import { SurfaceLoader } from "../../infra/helpers/surface_loader";
import { doctorCapabilityConfig } from "./capabilities/doctor/doctor.service";
import { initCapabilityConfig } from "./capabilities/init/init.service";
import { resetCapabilityConfig } from "./capabilities/reset/reset.service";

const moduleDirectory = dirname(fileURLToPath(import.meta.url));

export function createProjectSurface(): IModuleSurface {
  const loader = new SurfaceLoader(join(moduleDirectory, "surface"));

  return {
    moduleId: "project",
    capabilities: async () =>
      ResultValue.ok(
        surfaceCapabilitiesFromConfigs([
          doctorCapabilityConfig,
          initCapabilityConfig,
          resetCapabilityConfig,
        ]),
      ),
    knowledge: () => loader.knowledge(),
    loop: () => loader.loop(),
    prompt: (input?: SurfacePromptInput) => loader.prompt(input),
    skill: () => loader.skill(),
  };
}

export type ProjectSurfaceResult<T> = Result<AgentDevKitErrorCode, T>;
