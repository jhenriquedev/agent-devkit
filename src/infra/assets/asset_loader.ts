import { readFile } from "node:fs/promises";
import { join, relative, resolve } from "node:path";
import type { AssetKind, AssetReader } from "../bases/assets";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";

export type AssetLoaderOptions = {
  readonly rootDirectory: string;
};

const textDecoder = new TextDecoder();

export class AssetLoader implements AssetReader {
  readonly #rootDirectory: string;

  constructor(options: AssetLoaderOptions) {
    this.#rootDirectory = resolve(options.rootDirectory);
  }

  async loadBinary(
    kind: AssetKind,
    name: string,
  ): Promise<Result<AgentDevKitErrorCode, Uint8Array>> {
    const target = this.#resolve(kind, name);

    if (target.isErr()) {
      return Result.fail(target.unwrapError());
    }

    try {
      return Result.ok(await readFile(target.unwrap()));
    } catch {
      return Result.fail(ErrorCodes.AssetReadFailed);
    }
  }

  async loadJson<TValue>(
    kind: AssetKind,
    name: string,
  ): Promise<Result<AgentDevKitErrorCode, TValue>> {
    const content = await this.loadText(kind, name);

    if (content.isErr()) {
      return Result.fail(content.unwrapError());
    }

    try {
      return Result.ok(JSON.parse(content.unwrap()) as TValue);
    } catch {
      return Result.fail(ErrorCodes.InvalidInput);
    }
  }

  async loadText(kind: AssetKind, name: string): Promise<Result<AgentDevKitErrorCode, string>> {
    const binary = await this.loadBinary(kind, name);

    if (binary.isErr()) {
      return Result.fail(binary.unwrapError());
    }

    return Result.ok(textDecoder.decode(binary.unwrap()));
  }

  #resolve(kind: AssetKind, name: string): Result<AgentDevKitErrorCode, string> {
    const target = resolve(join(this.#rootDirectory, kind, name));
    const pathFromRoot = relative(this.#rootDirectory, target);

    if (pathFromRoot.startsWith("..") || pathFromRoot === "") {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    return Result.ok(target);
  }
}
