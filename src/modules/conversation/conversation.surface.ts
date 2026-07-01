import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Result } from "../../infra/bases/result";
import type { IModuleSurface, SurfacePromptInput } from "../../infra/bases/surface";
import { surfaceCapabilitiesFromConfigs } from "../../infra/helpers/surface_capabilities";
import { resolveModuleSurfaceDirectory, SurfaceLoader } from "../../infra/helpers/surface_loader";
import { conversationChatCapabilityConfig } from "./capabilities/chat/chat.service";

const moduleDirectory = dirname(fileURLToPath(import.meta.url));

export function createConversationSurface(): IModuleSurface {
  const loader = new SurfaceLoader(resolveModuleSurfaceDirectory("conversation", moduleDirectory));

  return {
    moduleId: "conversation",
    capabilities: async () =>
      Result.ok(surfaceCapabilitiesFromConfigs([conversationChatCapabilityConfig])),
    knowledge: () => loader.knowledge(),
    loop: () => loader.loop(),
    prompt: (input?: SurfacePromptInput) => loader.prompt(input),
    skill: () => loader.skill(),
  };
}
