import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import type { InstalledModel, ModelCatalogEntry } from "../../../../infra/bases/model";
import { Result } from "../../../../infra/bases/result";
import { ModelCatalogLoader } from "../../../../infra/models/model_catalog";
import { type ModelDownloadProgress, ModelStore } from "../../../../infra/models/model_store";
import type { ModelView } from "./registry.entities";

export type ModelInstallProgress = (progress: ModelDownloadProgress) => void;

export interface ModelsRegistryRepositoryPort extends CapabilityRepositoryPort {
  directory(): string;
  defaultId(): Promise<Result<AgentDevKitErrorCode, string | undefined>>;
  install(
    id: string,
    onProgress?: ModelInstallProgress,
  ): Promise<Result<AgentDevKitErrorCode, ModelView>>;
  listModels(): Promise<Result<AgentDevKitErrorCode, ModelView[]>>;
  setDefault(id: string): Promise<Result<AgentDevKitErrorCode, string>>;
  statusModels(id?: string): Promise<Result<AgentDevKitErrorCode, ModelView[]>>;
  uninstall(id: string): Promise<Result<AgentDevKitErrorCode, { id: string; removed: boolean }>>;
  update(id?: string): Promise<Result<AgentDevKitErrorCode, ModelView[]>>;
}

export type ModelsRegistryRepositoryOptions = {
  catalog?: ModelCatalogLoader;
  store?: ModelStore;
  stateDirectory?: string;
};

export class ModelsRegistryRepository implements ModelsRegistryRepositoryPort {
  readonly repositoryId = "models.registry.repository";
  readonly #catalog: ModelCatalogLoader;
  readonly #store: ModelStore;

  constructor(options: ModelsRegistryRepositoryOptions = {}) {
    this.#catalog = options.catalog ?? new ModelCatalogLoader();
    this.#store = options.store ?? new ModelStore({ stateDirectory: options.stateDirectory });
  }

  directory(): string {
    return this.#store.directory();
  }

  defaultId(): Promise<Result<AgentDevKitErrorCode, string | undefined>> {
    return this.#store.getDefault();
  }

  async listModels(): Promise<Result<AgentDevKitErrorCode, ModelView[]>> {
    const catalog = await this.#catalog.list();
    return catalog.isErr()
      ? Result.fail(catalog.unwrapError())
      : this.#buildViews(catalog.unwrap());
  }

  async statusModels(id?: string): Promise<Result<AgentDevKitErrorCode, ModelView[]>> {
    const catalog = await this.#catalog.list();

    if (catalog.isErr()) {
      return Result.fail(catalog.unwrapError());
    }

    const entries =
      id === undefined ? catalog.unwrap() : catalog.unwrap().filter((entry) => entry.id === id);

    if (id !== undefined && entries.length === 0) {
      return Result.fail(ErrorCodes.ModelNotFound);
    }

    return this.#buildViews(entries);
  }

  async install(
    id: string,
    onProgress?: ModelInstallProgress,
  ): Promise<Result<AgentDevKitErrorCode, ModelView>> {
    const entry = await this.#catalog.find(id);

    if (entry.isErr()) {
      return Result.fail(entry.unwrapError());
    }

    const installed = await this.#store.install(entry.unwrap(), { onProgress });

    if (installed.isErr()) {
      return Result.fail(installed.unwrapError());
    }

    const defaultId = await this.#store.getDefault();

    return Result.ok(
      this.#toView(
        entry.unwrap(),
        installed.unwrap(),
        defaultId.isOk() ? defaultId.unwrap() : undefined,
      ),
    );
  }

  async uninstall(
    id: string,
  ): Promise<Result<AgentDevKitErrorCode, { id: string; removed: boolean }>> {
    const removed = await this.#store.uninstall(id);

    return removed.isOk()
      ? Result.ok({ id, removed: removed.unwrap().removed })
      : Result.fail(removed.unwrapError());
  }

  async update(id?: string): Promise<Result<AgentDevKitErrorCode, ModelView[]>> {
    if (id !== undefined) {
      const view = await this.install(id);
      return view.isOk() ? Result.ok([view.unwrap()]) : Result.fail(view.unwrapError());
    }

    const installedIds = await this.#store.installedIds();

    if (installedIds.isErr()) {
      return Result.fail(installedIds.unwrapError());
    }

    const views: ModelView[] = [];

    for (const modelId of installedIds.unwrap()) {
      const entry = await this.#catalog.find(modelId);

      if (entry.isErr()) {
        continue;
      }

      const verified = await this.#store.verify(modelId, entry.unwrap().sha256);

      if (verified.isOk() && verified.unwrap() === false) {
        const repaired = await this.install(modelId);

        if (repaired.isOk()) {
          views.push(repaired.unwrap());
          continue;
        }
      }

      const status = await this.#store.status(modelId);
      const defaultId = await this.#store.getDefault();
      views.push(
        this.#toView(
          entry.unwrap(),
          status.isOk() ? status.unwrap() : undefined,
          defaultId.isOk() ? defaultId.unwrap() : undefined,
        ),
      );
    }

    return Result.ok(views);
  }

  async setDefault(id: string): Promise<Result<AgentDevKitErrorCode, string>> {
    const set = await this.#store.setDefault(id);
    return set.isOk() ? Result.ok(id) : Result.fail(set.unwrapError());
  }

  async #buildViews(
    entries: ModelCatalogEntry[],
  ): Promise<Result<AgentDevKitErrorCode, ModelView[]>> {
    const defaultId = await this.#store.getDefault();
    const resolvedDefault = defaultId.isOk() ? defaultId.unwrap() : undefined;
    const views: ModelView[] = [];

    for (const entry of entries) {
      const status = await this.#store.status(entry.id);
      views.push(this.#toView(entry, status.isOk() ? status.unwrap() : undefined, resolvedDefault));
    }

    return Result.ok(views);
  }

  #toView(
    entry: ModelCatalogEntry,
    installed: InstalledModel | undefined,
    defaultId: string | undefined,
  ): ModelView {
    return {
      id: entry.id,
      name: entry.name,
      family: entry.family,
      parameters: entry.parameters,
      quantization: entry.quantization,
      sizeBytes: installed?.sizeBytes ?? entry.sizeBytes,
      contextLength: entry.contextLength,
      license: entry.license,
      recommended: entry.recommended,
      installed: installed !== undefined,
      isDefault: defaultId === entry.id,
      path: installed?.path,
    };
  }
}
