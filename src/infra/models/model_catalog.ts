import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { AssetLoader } from "../assets/asset_loader";
import type { AssetReader } from "../bases/assets";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { type ModelCatalog, type ModelCatalogEntry, ModelCatalogSchema } from "../bases/model";
import { Result } from "../bases/result";

export type ModelCatalogLoaderOptions = {
  loader?: AssetReader;
};

function defaultAssetsRoot(): string {
  const moduleDirectory = dirname(fileURLToPath(import.meta.url));
  const candidates = [
    resolve(moduleDirectory, "../../assets"),
    resolve(moduleDirectory, "../src/assets"),
    resolve(process.cwd(), "src/assets"),
  ];

  return (
    candidates.find((candidate) => existsSync(candidate)) ?? resolve(process.cwd(), "src/assets")
  );
}

export class ModelCatalogLoader {
  readonly #loader: AssetReader;
  #catalog?: ModelCatalog;

  constructor(options: ModelCatalogLoaderOptions = {}) {
    this.#loader = options.loader ?? new AssetLoader({ rootDirectory: defaultAssetsRoot() });
  }

  async load(): Promise<Result<AgentDevKitErrorCode, ModelCatalog>> {
    if (this.#catalog !== undefined) {
      return Result.ok(this.#catalog);
    }

    const payload = await this.#loader.loadJson<unknown>("models", "catalog.json");

    if (payload.isErr()) {
      return Result.fail(payload.unwrapError());
    }

    const parsed = ModelCatalogSchema.safeParse(payload.unwrap());

    if (!parsed.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    this.#catalog = parsed.data;
    return Result.ok(this.#catalog);
  }

  async list(): Promise<Result<AgentDevKitErrorCode, ModelCatalogEntry[]>> {
    return (await this.load()).map((catalog) => catalog.models);
  }

  async find(id: string): Promise<Result<AgentDevKitErrorCode, ModelCatalogEntry>> {
    const catalog = await this.load();

    if (catalog.isErr()) {
      return Result.fail(catalog.unwrapError());
    }

    const entry = catalog.unwrap().models.find((model) => model.id === id);
    return entry === undefined ? Result.fail(ErrorCodes.ModelNotFound) : Result.ok(entry);
  }

  async recommended(): Promise<Result<AgentDevKitErrorCode, ModelCatalogEntry | undefined>> {
    const catalog = await this.load();

    if (catalog.isErr()) {
      return Result.fail(catalog.unwrapError());
    }

    const models = catalog.unwrap().models;
    return Result.ok(models.find((model) => model.recommended) ?? models[0]);
  }
}
