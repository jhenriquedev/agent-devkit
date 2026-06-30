export type AgentDevKitConfig = {
  readonly description: string;
  readonly id: string;
  readonly name: string;
};

export function defineConfig<TConfig extends AgentDevKitConfig>(config: TConfig): TConfig {
  return config;
}
