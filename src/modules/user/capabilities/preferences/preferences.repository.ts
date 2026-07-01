import { existsSync } from "node:fs";
import { access, readdir, readFile } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import type { AgentDataStore } from "../../../../infra/bases/data_store";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import type { LanguageDefinition } from "../../../../infra/bases/i18n";
import { Result } from "../../../../infra/bases/result";
import { type ThemeDefinition, ThemeDefinitionSchema } from "../../../../infra/bases/theme";
import { LocalAgentDataStore } from "../../../../infra/data/local_agent_data_store";
import type { UserPreferences } from "./preferences.entities";

export type PreferencesRepositoryOptions = {
  dataStore?: AgentDataStore;
  homeDirectory?: string;
  i18nDirectory?: string;
  themesDirectory?: string;
};

export interface PreferencesRepositoryPort extends CapabilityRepositoryPort {
  defaultPreferences(): UserPreferences;
  loadLanguages(): Promise<Result<AgentDevKitErrorCode, LanguageDefinition[]>>;
  loadPreferences(): Promise<Result<AgentDevKitErrorCode, UserPreferences>>;
  loadThemes(): Promise<Result<AgentDevKitErrorCode, ThemeDefinition[]>>;
  preferencesPath(): string;
  savePreferences(preferences: UserPreferences): Promise<Result<AgentDevKitErrorCode, void>>;
}

const defaultLanguage = "pt-BR";
const defaultLogRetentionDays = 30;
const defaultTheme = "default-purple";

function defaultThemesDirectory(): string {
  const moduleDirectory = dirname(fileURLToPath(import.meta.url));
  const candidates = [
    resolve(moduleDirectory, "../../../../assets/themes"),
    resolve(moduleDirectory, "../src/assets/themes"),
    resolve(process.cwd(), "src/assets/themes"),
  ];

  return (
    candidates.find((candidate) => existsSync(candidate)) ??
    resolve(process.cwd(), "src/assets/themes")
  );
}

function createDefaultPreferences(): UserPreferences {
  return {
    schema: "agent-devkit.user-preferences/v1",
    language: defaultLanguage,
    logRetentionDays: defaultLogRetentionDays,
    theme: defaultTheme,
    updatedAt: new Date(0).toISOString(),
  };
}

export class PreferencesRepository implements PreferencesRepositoryPort {
  readonly repositoryId = "user.preferences.repository";
  readonly #dataStore: AgentDataStore;
  readonly #homeDirectory: string;
  readonly #i18nCatalog: I18nCatalog;
  readonly #themesDirectory: string;

  constructor(options: PreferencesRepositoryOptions = {}) {
    this.#homeDirectory = options.homeDirectory ?? homedir();
    this.#dataStore =
      options.dataStore ??
      new LocalAgentDataStore({
        rootDirectory: join(this.#homeDirectory, ".agent-devkit", "data"),
      });
    this.#i18nCatalog = new I18nCatalog({ directory: options.i18nDirectory });
    this.#themesDirectory = options.themesDirectory ?? defaultThemesDirectory();
  }

  defaultPreferences(): UserPreferences {
    return createDefaultPreferences();
  }

  async loadLanguages(): Promise<Result<AgentDevKitErrorCode, LanguageDefinition[]>> {
    return this.#i18nCatalog.loadLanguages();
  }

  async loadPreferences(): Promise<Result<AgentDevKitErrorCode, UserPreferences>> {
    const path = { namespace: "preferences" as const, segments: ["preferences.json"] };
    const exists = await this.#dataStore.exists(path);

    if (exists.isErr()) {
      return Result.fail(exists.unwrapError());
    }

    if (exists.unwrap()) {
      const payload = await this.#dataStore.readJson<Partial<UserPreferences>>(path);

      if (payload.isErr()) {
        return Result.fail(payload.unwrapError());
      }

      return this.#normalizePayload(payload.unwrap());
    }

    const legacy = await this.#loadLegacyPreferences();

    if (legacy.isOk()) {
      await this.savePreferences(legacy.unwrap());
      return legacy;
    }

    if (legacy.unwrapError() !== ErrorCodes.FileReadFailed) {
      return Result.fail(legacy.unwrapError());
    }

    return Result.ok(this.defaultPreferences());
  }

  async #loadLegacyPreferences(): Promise<Result<AgentDevKitErrorCode, UserPreferences>> {
    try {
      await access(this.#legacyPreferencesPath());
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }

    try {
      const payload = JSON.parse(
        await readFile(this.#legacyPreferencesPath(), "utf8"),
      ) as Partial<UserPreferences>;
      return this.#normalizePayload(payload);
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  #normalizePayload(
    payload: Partial<UserPreferences>,
  ): Result<AgentDevKitErrorCode, UserPreferences> {
    if (payload.schema !== "agent-devkit.user-preferences/v1") {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    return Result.ok({
      schema: "agent-devkit.user-preferences/v1",
      language: payload.language ?? defaultLanguage,
      logRetentionDays: payload.logRetentionDays ?? defaultLogRetentionDays,
      theme: payload.theme ?? defaultTheme,
      updatedAt: payload.updatedAt ?? new Date(0).toISOString(),
    });
  }

  async loadThemes(): Promise<Result<AgentDevKitErrorCode, ThemeDefinition[]>> {
    try {
      const files = (await readdir(this.#themesDirectory))
        .filter((file) => file.endsWith(".json"))
        .sort((left, right) =>
          left === "default-purple.json"
            ? -1
            : right === "default-purple.json"
              ? 1
              : left.localeCompare(right),
        );
      const themes: ThemeDefinition[] = [];

      for (const file of files) {
        const payload = JSON.parse(await readFile(join(this.#themesDirectory, file), "utf8"));
        const parsed = ThemeDefinitionSchema.safeParse(payload);

        if (!parsed.success) {
          return Result.fail(ErrorCodes.InvalidInput);
        }

        themes.push(parsed.data);
      }

      return Result.ok(themes);
    } catch {
      return Result.fail(ErrorCodes.AssetReadFailed);
    }
  }

  preferencesPath(): string {
    const resolved = this.#dataStore.resolve({
      namespace: "preferences",
      segments: ["preferences.json"],
    });

    return resolved.isOk()
      ? resolved.unwrap()
      : join(this.#homeDirectory, ".agent-devkit", "data", "preferences", "preferences.json");
  }

  async savePreferences(preferences: UserPreferences): Promise<Result<AgentDevKitErrorCode, void>> {
    return this.#dataStore.writeJson(
      { namespace: "preferences", segments: ["preferences.json"] },
      preferences,
    );
  }

  #legacyPreferencesPath(): string {
    return join(this.#homeDirectory, ".agent-devkit", "preferences.json");
  }
}
