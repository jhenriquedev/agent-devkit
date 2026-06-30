import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { IModuleSurface, SurfacePromptInput } from "../../infra/bases/surface";
import { SurfaceLoader } from "../../infra/helpers/surface_loader";

const moduleDirectory = dirname(fileURLToPath(import.meta.url));

export function createSelfSurface(): IModuleSurface {
  const loader = new SurfaceLoader(join(moduleDirectory, "surface"));

  return {
    moduleId: "self",
    capabilities: () => loader.capabilities(),
    knowledge: () => loader.knowledge(),
    loop: () => loader.loop(),
    prompt: (input?: SurfacePromptInput) => loader.prompt(input),
    skill: () => loader.skill(),
  };
}
