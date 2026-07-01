import type { InvokableCapabilityService } from "../infra/bases/capability";
import type { AgentDevKitErrorCode } from "../infra/bases/errors";
import { Result } from "../infra/bases/result";
import {
  type CapabilityRegistry,
  createCapabilityRegistry,
} from "../infra/capabilities/capability_registry";
import { type AgentModuleRegistryOptions, agentModuleDefinitions } from "./modules.registry";

export type AgentCapabilityRegistryOptions = AgentModuleRegistryOptions;

export function createAgentCapabilityRegistry(
  options: AgentCapabilityRegistryOptions,
): Result<AgentDevKitErrorCode, CapabilityRegistry> {
  const capabilities: InvokableCapabilityService[] = [];

  for (const definition of agentModuleDefinitions) {
    const binding = definition.bind(options);
    if (binding.isErr()) {
      return Result.fail(binding.unwrapError());
    }

    capabilities.push(...definition.capabilities(binding.unwrap()));
  }

  return createCapabilityRegistry({
    capabilities,
  });
}
