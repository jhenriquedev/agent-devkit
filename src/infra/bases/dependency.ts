import type { AgentDevKitErrorCode } from "./errors";
import type { Result } from "./result";

export type DependencyId = string;

export type DependencyAction =
  | "check"
  | "check-compatibility"
  | "check-environment"
  | "check-installed"
  | "configure"
  | "downgrade"
  | "install"
  | "list"
  | "plan-configure"
  | "plan-downgrade"
  | "plan-install"
  | "plan-uninstall"
  | "plan-upgrade"
  | "uninstall"
  | "upgrade"
  | "verify";

export type DependencyStatus =
  | "compatible"
  | "configured"
  | "incompatible"
  | "installed"
  | "missing"
  | "ok"
  | "planned"
  | "unsupported"
  | "warning";

export type DependencyRisk = "read-only" | "writes-external" | "writes-global-state";

export type DependencyMetadata = {
  category: string;
  description: string;
  id: DependencyId;
  name: string;
  risk: DependencyRisk;
};

export type DependencyCheck = {
  details?: Record<string, unknown>;
  id: DependencyId;
  message: string;
  status: DependencyStatus;
};

export type DependencyCommandPlan = {
  command: string;
  description: string;
  risk: DependencyRisk;
};

export type DependencyPlan = {
  commands: DependencyCommandPlan[];
  id: DependencyId;
  message: string;
  requiresApproval: boolean;
  status: DependencyStatus;
};

export type DependencyOperationResult = {
  id: DependencyId;
  message: string;
  status: DependencyStatus;
};

export type DependencyProviderOptions = {
  options?: Record<string, unknown>;
  version?: string;
};

export interface DependencyProvider {
  checkCompatibility(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck>>;
  checkEnvironment(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck>>;
  checkInstalled(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck>>;
  configure(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyOperationResult>>;
  downgrade(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyOperationResult>>;
  install(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyOperationResult>>;
  metadata(): DependencyMetadata;
  planConfigure(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyPlan>>;
  planDowngrade(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyPlan>>;
  planInstall(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyPlan>>;
  planUninstall(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyPlan>>;
  planUpgrade(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyPlan>>;
  uninstall(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyOperationResult>>;
  upgrade(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyOperationResult>>;
  verify(
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck>>;
}
