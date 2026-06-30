import type { BaseCapabilityService, CapabilityConfig } from "./capability";
import type { AgentDevKitErrorCode } from "./errors";
import type { AgentDevKitModuleConfig } from "./module";
import { Result } from "./result";

export type ModuleCapabilityMap = Record<string, BaseCapabilityService<CapabilityConfig, unknown>>;

export type ModuleBinding<
  TConfig extends AgentDevKitModuleConfig,
  TCapabilities extends ModuleCapabilityMap,
> = {
  readonly capabilities: TCapabilities;
  readonly config: TConfig;
};

export abstract class ModuleBinder<
  TOptions,
  TConfig extends AgentDevKitModuleConfig,
  TCapabilities extends ModuleCapabilityMap,
> {
  abstract bind(
    options: TOptions,
  ): Result<AgentDevKitErrorCode, ModuleBinding<TConfig, TCapabilities>>;
}

export function defineModuleBinding<
  TConfig extends AgentDevKitModuleConfig,
  TCapabilities extends ModuleCapabilityMap,
>(
  binding: ModuleBinding<TConfig, TCapabilities>,
): Result<AgentDevKitErrorCode, ModuleBinding<TConfig, TCapabilities>> {
  return Result.ok(binding);
}
