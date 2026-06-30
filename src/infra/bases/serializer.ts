import type { AgentDevKitErrorCode } from "./errors";
import type { Result } from "./result";

export type SerializedFileFormat = "json" | "md" | "pdf" | "txt";

export interface FileSerializer<TValue = unknown> {
  readonly format: SerializedFileFormat;
  deserialize(content: Uint8Array): Promise<Result<AgentDevKitErrorCode, TValue>>;
  serialize(value: TValue): Promise<Result<AgentDevKitErrorCode, Uint8Array>>;
}

export interface FileSerializerResolver {
  deserialize<TValue>(
    format: SerializedFileFormat,
    content: Uint8Array,
  ): Promise<Result<AgentDevKitErrorCode, TValue>>;
  serialize(
    format: SerializedFileFormat,
    value: unknown,
  ): Promise<Result<AgentDevKitErrorCode, Uint8Array>>;
}
