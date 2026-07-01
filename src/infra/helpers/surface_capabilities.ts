import type { CapabilityConfig } from "../bases/capability";
import type { SurfaceCapability } from "../bases/surface";

export function surfaceCapabilitiesFromConfigs(
  configs: readonly CapabilityConfig[],
): SurfaceCapability[] {
  return configs.map((config) => ({
    id: config.id,
    kind: config.kind,
    risk: config.risk,
    summary: config.description,
    title: config.name,
  }));
}
