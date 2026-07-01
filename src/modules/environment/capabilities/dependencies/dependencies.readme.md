# Environment Dependencies Capability

`environment.dependencies` manages the lifecycle contract for external
dependencies known by Agent DevKit.

The capability is provider-based. Providers define how a dependency is checked,
planned, configured, installed, upgraded, downgraded and removed. This first
provider is `node`, which is read-only and does not install or remove anything.

No arbitrary shell command execution is allowed through this capability.
