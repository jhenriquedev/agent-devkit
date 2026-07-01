import { ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import type { ModelView } from "./registry.entities";
import type { ModelsRegistryRepositoryPort } from "./registry.repository";
import { ModelsRegistryService } from "./registry.service";

function view(overrides: Partial<ModelView> = {}): ModelView {
  return {
    id: "qwen2.5-0.5b-instruct-q4_k_m",
    name: "Qwen2.5 0.5B Instruct",
    family: "qwen2.5",
    parameters: "0.5B",
    quantization: "Q4_K_M",
    sizeBytes: 491000000,
    contextLength: 32768,
    license: "Apache-2.0",
    recommended: true,
    installed: false,
    isDefault: false,
    ...overrides,
  };
}

function repository(
  overrides: Partial<ModelsRegistryRepositoryPort> = {},
): ModelsRegistryRepositoryPort {
  return {
    repositoryId: "test.models.registry",
    directory: () => "/home/user/.agent-devkit/models",
    defaultId: async () => Result.ok(undefined),
    install: async (id) => Result.ok(view({ id, installed: true })),
    listModels: async () => Result.ok([view()]),
    setDefault: async (id) => Result.ok(id),
    statusModels: async () => Result.ok([view()]),
    uninstall: async (id) => Result.ok({ id, removed: true }),
    update: async () => Result.ok([view()]),
    ...overrides,
  };
}

function service(overrides?: Partial<ModelsRegistryRepositoryPort>): ModelsRegistryService {
  return new ModelsRegistryService({ repository: repository(overrides) });
}

describe("models.registry", () => {
  it("lists catalog models with the store directory", async () => {
    const result = await service().execute({ action: "list" });

    expect(result.isOk()).toBe(true);
    expect(result.unwrap()).toMatchObject({
      action: "list",
      directory: "/home/user/.agent-devkit/models",
    });
  });

  it("installs a model by id", async () => {
    const result = await service().execute({
      action: "install",
      id: "qwen2.5-0.5b-instruct-q4_k_m",
    });

    expect(result.isOk()).toBe(true);
    const payload = result.unwrap();

    if (payload.action !== "install") {
      throw new Error("Expected install result.");
    }

    expect(payload.model.installed).toBe(true);
  });

  it("selects a default model", async () => {
    const result = await service().execute({
      action: "use",
      id: "qwen2.5-0.5b-instruct-q4_k_m",
    });

    expect(result.isOk()).toBe(true);
    expect(result.unwrap()).toMatchObject({
      action: "use",
      defaultId: "qwen2.5-0.5b-instruct-q4_k_m",
    });
  });

  it("propagates repository failures", async () => {
    const result = await service({
      install: async () => Result.fail(ErrorCodes.ModelNotFound),
    }).execute({ action: "install", id: "missing" });

    expect(result.isErr()).toBe(true);
    expect(result.unwrapError()).toBe(ErrorCodes.ModelNotFound);
  });

  it("rejects invalid input before dispatching", async () => {
    const result = await service().execute({ action: "missing" } as never);

    expect(result.isErr()).toBe(true);
    expect(result.unwrapError()).toBe(ErrorCodes.InvalidInput);
  });

  it("requires approval only for model write actions", () => {
    const registry = service();

    expect(registry.approvalForInput({ action: "list" })).toEqual({
      reason: "Models registry read action.",
      required: false,
    });
    expect(registry.effectsForInput({ action: "status" })).toEqual([
      { operation: "read", scope: "none" },
    ]);
    expect(registry.approvalForInput({ action: "install", id: "model" })).toEqual({
      reason: "Models registry action writes local model state.",
      required: true,
    });
    expect(registry.effectsForInput({ action: "uninstall", id: "model" })).toEqual([
      { operation: "delete", scope: "global" },
    ]);
  });
});
