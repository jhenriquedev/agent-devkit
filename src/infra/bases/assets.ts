import type { AgentDevKitErrorCode } from "./errors";
import type { Result } from "./result";

export type AssetKind = "fonts" | "i18n" | "images" | "themes";

export type LoadedAsset<TContent> = {
  readonly content: TContent;
  readonly kind: AssetKind;
  readonly name: string;
  readonly path: string;
};

export interface AssetReader {
  loadBinary(kind: AssetKind, name: string): Promise<Result<AgentDevKitErrorCode, Uint8Array>>;
  loadJson<TValue>(kind: AssetKind, name: string): Promise<Result<AgentDevKitErrorCode, TValue>>;
  loadText(kind: AssetKind, name: string): Promise<Result<AgentDevKitErrorCode, string>>;
}
