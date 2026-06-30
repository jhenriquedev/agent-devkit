import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, extname, join, relative, resolve } from "node:path";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";
import type { SerializedFileFormat } from "../bases/serializer";
import { FileSerializerRegistry } from "./file_serializers";

export type SerializedFileStoreOptions = {
  readonly rootDirectory: string;
  readonly serializers?: FileSerializerRegistry;
};

export class SerializedFileStore {
  readonly #rootDirectory: string;
  readonly #serializers: FileSerializerRegistry;

  constructor(options: SerializedFileStoreOptions) {
    this.#rootDirectory = resolve(options.rootDirectory);
    this.#serializers = options.serializers ?? FileSerializerRegistry.withDefaults();
  }

  async read<TValue>(path: string): Promise<Result<AgentDevKitErrorCode, TValue>> {
    const target = this.#resolve(path);

    if (target.isErr()) {
      return Result.fail(target.unwrapError());
    }

    try {
      const content = await readFile(target.unwrap());
      return this.#serializers.deserialize(this.#format(path), content);
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  async write(path: string, value: unknown): Promise<Result<AgentDevKitErrorCode, void>> {
    const target = this.#resolve(path);

    if (target.isErr()) {
      return Result.fail(target.unwrapError());
    }

    const content = await this.#serializers.serialize(this.#format(path), value);

    if (content.isErr()) {
      return Result.fail(content.unwrapError());
    }

    try {
      await mkdir(dirname(target.unwrap()), { recursive: true });
      await writeFile(target.unwrap(), content.unwrap());
      return Result.ok(undefined);
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }

  #format(path: string): SerializedFileFormat {
    return extname(path).slice(1) as SerializedFileFormat;
  }

  #resolve(path: string): Result<AgentDevKitErrorCode, string> {
    const target = resolve(join(this.#rootDirectory, path));
    const pathFromRoot = relative(this.#rootDirectory, target);

    if (pathFromRoot.startsWith("..") || pathFromRoot === "") {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    return Result.ok(target);
  }
}
