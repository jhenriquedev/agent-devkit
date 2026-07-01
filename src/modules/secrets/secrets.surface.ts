import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Result } from "../../infra/bases/result";
import type { IModuleSurface, SurfacePromptInput } from "../../infra/bases/surface";
import { surfaceCapabilitiesFromConfigs } from "../../infra/helpers/surface_capabilities";
import { resolveModuleSurfaceDirectory, SurfaceLoader } from "../../infra/helpers/surface_loader";
import { secretsVaultCapabilityConfig } from "./capabilities/vault/vault.service";

const moduleDirectory = dirname(fileURLToPath(import.meta.url));

export function createSecretsSurface(): IModuleSurface {
  const loader = new SurfaceLoader(resolveModuleSurfaceDirectory("secrets", moduleDirectory));

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
