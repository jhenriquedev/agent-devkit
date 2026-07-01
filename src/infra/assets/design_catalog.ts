import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { AssetReader } from "../bases/assets";
import {
  type DesignSemantics,
  DesignSemanticsSchema,
  type KitSprite,
  KitSpriteSchema,
} from "../bases/design";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";
import { AssetLoader } from "./asset_loader";

export type DesignCatalogOptions = {
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

export class DesignCatalog {
  readonly #loader: AssetReader;
  #semantics?: DesignSemantics;
  #kit?: KitSprite;

  constructor(options: DesignCatalogOptions = {}) {
    this.#loader = options.loader ?? new AssetLoader({ rootDirectory: defaultAssetsRoot() });
  }

  async semantics(): Promise<Result<AgentDevKitErrorCode, DesignSemantics>> {
    if (this.#semantics !== undefined) {
      return Result.ok(this.#semantics);
    }

    const payload = await this.#loader.loadJson<unknown>("design", "semantics.json");

    if (payload.isErr()) {
      return Result.fail(payload.unwrapError());
    }

    const parsed = DesignSemanticsSchema.safeParse(payload.unwrap());

    if (!parsed.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    this.#semantics = parsed.data;
    return Result.ok(this.#semantics);
  }

  async kit(): Promise<Result<AgentDevKitErrorCode, KitSprite>> {
    if (this.#kit !== undefined) {
      return Result.ok(this.#kit);
    }

    const payload = await this.#loader.loadJson<unknown>("design", "kit.json");

    if (payload.isErr()) {
      return Result.fail(payload.unwrapError());
    }

    const parsed = KitSpriteSchema.safeParse(payload.unwrap());

    if (!parsed.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    this.#kit = parsed.data;
    return Result.ok(this.#kit);
  }
}
