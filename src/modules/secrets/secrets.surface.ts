import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { Result } from "../../infra/bases/result";
import type { IModuleSurface, SurfacePromptInput } from "../../infra/bases/surface";
import { surfaceCapabilitiesFromConfigs } from "../../infra/helpers/surface_capabilities";
import { SurfaceLoader } from "../../infra/helpers/surface_loader";
import { secretsVaultCapabilityConfig } from "./capabilities/vault/vault.service";

const moduleDirectory = dirname(fileURLToPath(import.meta.url));

export function createSecretsSurface(): IModuleSurface {
  const loader = new SurfaceLoader(join(moduleDirectory, "surface"));

  return {
    moduleId: "secrets",
    capabilities: async () =>
      Result.ok(surfaceCapabilitiesFromConfigs([secretsVaultCapabilityConfig])),
    knowledge: () => loader.knowledge(),
    loop: () => loader.loop(),
    prompt: (input?: SurfacePromptInput) => loader.prompt(input),
    skill: () => loader.skill(),
  };
}
