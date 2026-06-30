import type { AgentDevKitErrorCode } from "../bases/errors";
import { ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";
import type { FileSerializer, SerializedFileFormat } from "../bases/serializer";

const textDecoder = new TextDecoder();
const textEncoder = new TextEncoder();

export class JsonFileSerializer implements FileSerializer<unknown> {
  readonly format = "json" as const;

  async deserialize(content: Uint8Array): Promise<Result<AgentDevKitErrorCode, unknown>> {
    try {
      return Result.ok(JSON.parse(textDecoder.decode(content)) as unknown);
    } catch {
      return Result.fail(ErrorCodes.InvalidInput);
    }
  }

  async serialize(value: unknown): Promise<Result<AgentDevKitErrorCode, Uint8Array>> {
    try {
      return Result.ok(textEncoder.encode(`${JSON.stringify(value, null, 2)}\n`));
    } catch {
      return Result.fail(ErrorCodes.InvalidInput);
    }
  }
}

export class TextFileSerializer implements FileSerializer<string> {
  readonly format = "txt" as const;

  async deserialize(content: Uint8Array): Promise<Result<AgentDevKitErrorCode, string>> {
    return Result.ok(textDecoder.decode(content));
  }

  async serialize(value: string): Promise<Result<AgentDevKitErrorCode, Uint8Array>> {
    return typeof value === "string"
      ? Result.ok(textEncoder.encode(value))
      : Result.fail(ErrorCodes.InvalidInput);
  }
}

export class MarkdownFileSerializer implements FileSerializer<string> {
  readonly format = "md" as const;

  async deserialize(content: Uint8Array): Promise<Result<AgentDevKitErrorCode, string>> {
    return Result.ok(textDecoder.decode(content));
  }

  async serialize(value: string): Promise<Result<AgentDevKitErrorCode, Uint8Array>> {
    return typeof value === "string"
      ? Result.ok(textEncoder.encode(value))
      : Result.fail(ErrorCodes.InvalidInput);
  }
}

export class PdfFileSerializer implements FileSerializer<Uint8Array> {
  readonly format = "pdf" as const;

  async deserialize(content: Uint8Array): Promise<Result<AgentDevKitErrorCode, Uint8Array>> {
    return Result.ok(content);
  }

  async serialize(value: Uint8Array): Promise<Result<AgentDevKitErrorCode, Uint8Array>> {
    return value instanceof Uint8Array ? Result.ok(value) : Result.fail(ErrorCodes.InvalidInput);
  }
}

export class FileSerializerRegistry {
  readonly #serializers: Map<SerializedFileFormat, FileSerializer>;

  constructor(serializers: FileSerializer[]) {
    this.#serializers = new Map(serializers.map((serializer) => [serializer.format, serializer]));
  }

  static withDefaults(): FileSerializerRegistry {
    return new FileSerializerRegistry([
      new JsonFileSerializer(),
      new TextFileSerializer(),
      new MarkdownFileSerializer(),
      new PdfFileSerializer(),
    ]);
  }

  async deserialize<TValue>(
    format: SerializedFileFormat,
    content: Uint8Array,
  ): Promise<Result<AgentDevKitErrorCode, TValue>> {
    const serializer = this.#serializers.get(format);

    if (serializer === undefined) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const result = await serializer.deserialize(content);
    return result.isOk() ? Result.ok(result.unwrap() as TValue) : Result.fail(result.unwrapError());
  }

  async serialize(
    format: SerializedFileFormat,
    value: unknown,
  ): Promise<Result<AgentDevKitErrorCode, Uint8Array>> {
    const serializer = this.#serializers.get(format);

    if (serializer === undefined) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    return serializer.serialize(value as never);
  }
}
