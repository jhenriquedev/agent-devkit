import type { AgentDevKitConfig } from "./config";

export type ModuleTestBinding = {
  include: readonly [string, ...string[]];
};

export type AgentDevKitModuleConfig = AgentDevKitConfig & {
  capabilities: readonly string[];
  tests: ModuleTestBinding;
};

export function defineModuleConfig<TConfig extends AgentDevKitModuleConfig>(
  config: TConfig,
): TConfig {
  return config;
}
