import type { AgentDevKitErrorCode } from "./errors";
import type { Result } from "./result";

export type AgentDataNamespace = "context" | "logs" | "personalization" | "preferences" | "secrets";

export type AgentDataPath = {
  namespace: AgentDataNamespace;
  segments: string[];
};

export type AgentDataEntry = {
  kind: "directory" | "file";
  name: string;
  path: AgentDataPath;
};

export type AgentDataWriteOptions = {
  atomic?: boolean;
  encrypted?: boolean;
};

export type AgentDataNamespacePolicy = {
  encrypted: boolean;
};

export interface AgentDataStore {
  appendJsonl<T>(
    path: AgentDataPath,
    value: T,
    options?: AgentDataWriteOptions,
  ): Promise<Result<AgentDevKitErrorCode, void>>;
  exists(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, boolean>>;
  list(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, AgentDataEntry[]>>;
  readBinary(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, Uint8Array>>;
  readJson<T>(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, T>>;
  readJsonl<T>(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, T[]>>;
  readText(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, string>>;
  remove(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, void>>;
  resolve(path: AgentDataPath): Result<AgentDevKitErrorCode, string>;
  rootDirectory(): string;
  writeBinary(
    path: AgentDataPath,
    value: Uint8Array,
    options?: AgentDataWriteOptions,
  ): Promise<Result<AgentDevKitErrorCode, void>>;
  writeJson<T>(
    path: AgentDataPath,
    value: T,
    options?: AgentDataWriteOptions,
  ): Promise<Result<AgentDevKitErrorCode, void>>;
  writeText(
    path: AgentDataPath,
    value: string,
    options?: AgentDataWriteOptions,
  ): Promise<Result<AgentDevKitErrorCode, void>>;
}

const policies: Record<AgentDataNamespace, AgentDataNamespacePolicy> = {
  context: { encrypted: false },
  logs: { encrypted: false },
  personalization: { encrypted: false },
  preferences: { encrypted: false },
  secrets: { encrypted: true },
};

export function agentDataNamespacePolicy(namespace: AgentDataNamespace): AgentDataNamespacePolicy {
  return policies[namespace];
}
