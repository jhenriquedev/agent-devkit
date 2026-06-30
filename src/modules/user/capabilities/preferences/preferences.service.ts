import {
  BaseCapabilityService,
  type CapabilityExecution,
  defineCapabilityConfig,
} from "../../../../infra/bases/capability";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import type {
  PreferencesResult,
  PreferencesServiceOptions,
  UserPreferences,
} from "./preferences.entities";
import type { PreferencesRepositoryPort } from "./preferences.repository";

type PreferencesServiceDependencies = {
  repository: PreferencesRepositoryPort;
};

function isValidRetentionDays(value: number | undefined): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 1 && value <= 3650;
}

export const preferencesCapabilityConfig = defineCapabilityConfig({
  id: "user.preferences",
  moduleId: "user",
  name: "Preferences",
  description: "Read and update user Agent DevKit preferences.",
  kind: "deterministic",
  risk: "writes-global-state",
} as const);

export class PreferencesService
  extends BaseCapabilityService<typeof preferencesCapabilityConfig, PreferencesServiceDependencies>
  implements CapabilityExecution<PreferencesServiceOptions, PreferencesResult>
{
  readonly #repository: PreferencesRepositoryPort;

  constructor(dependencies: PreferencesServiceDependencies) {
    super(preferencesCapabilityConfig, dependencies);
    this.#repository = dependencies.repository;
  }

  async execute(
    options: PreferencesServiceOptions,
  ): Promise<Result<AgentDevKitErrorCode, PreferencesResult>> {
    const themes = await this.#repository.loadThemes();
    const languages = await this.#repository.loadLanguages();

    if (themes.isErr()) {
      return Result.fail(themes.unwrapError());
    }

    if (languages.isErr()) {
      return Result.fail(languages.unwrapError());
    }

    const availableThemes = themes.unwrap();
    const availableLanguages = languages.unwrap();
    const existing = await this.#repository.loadPreferences();

    if (existing.isErr()) {
      return Result.fail(existing.unwrapError());
    }

    let preferences = existing.unwrap();
    let status: PreferencesResult["status"] = "view";

    if (options.action === "reset-defaults") {
      preferences = {
        ...this.#repository.defaultPreferences(),
        updatedAt: new Date().toISOString(),
      };
      status = "reset";
    }

    if (options.action === "set-theme" || options.action === "update") {
      if (options.theme === undefined) {
        if (options.action === "set-theme") {
          return Result.fail(ErrorCodes.InvalidInput);
        }
      } else {
        if (!availableThemes.some((theme) => theme.id === options.theme)) {
          return Result.fail(ErrorCodes.InvalidInput);
        }

        preferences = {
          ...preferences,
          theme: options.theme,
          updatedAt: new Date().toISOString(),
        };
        status = "updated";
      }
    }

    if (options.action === "set-language" || options.action === "update") {
      if (options.language === undefined) {
        if (options.action === "set-language") {
          return Result.fail(ErrorCodes.InvalidInput);
        }
      } else {
        if (!availableLanguages.some((language) => language.id === options.language)) {
          return Result.fail(ErrorCodes.InvalidInput);
        }

        preferences = {
          ...preferences,
          language: options.language,
          updatedAt: new Date().toISOString(),
        };
        status = "updated";
      }
    }

    if (options.action === "set-log-retention" || options.action === "update") {
      if (options.logRetentionDays === undefined) {
        if (options.action === "set-log-retention") {
          return Result.fail(ErrorCodes.InvalidInput);
        }
      } else {
        if (!isValidRetentionDays(options.logRetentionDays)) {
          return Result.fail(ErrorCodes.InvalidInput);
        }

        preferences = {
          ...preferences,
          logRetentionDays: options.logRetentionDays,
          updatedAt: new Date().toISOString(),
        };
        status = "updated";
      }
    }

    if (status === "updated" || status === "reset") {
      const save = await this.#repository.savePreferences(preferences);

      if (save.isErr()) {
        return Result.fail(save.unwrapError());
      }
    }

    const activeTheme =
      availableThemes.find((theme) => theme.id === preferences.theme) ?? availableThemes[0];
    const activeLanguage =
      availableLanguages.find((language) => language.id === preferences.language) ??
      availableLanguages[0];

    if (activeTheme === undefined || activeLanguage === undefined) {
      return Result.fail(ErrorCodes.AssetReadFailed);
    }

    return Result.ok({
      activeLanguage,
      activeTheme,
      languages: availableLanguages.map((language) => ({
        id: language.id,
        name: language.name,
        nativeName: language.nativeName,
        selected: language.id === activeLanguage.id,
      })),
      path: this.#repository.preferencesPath(),
      preferences: this.#normalizePreferences(preferences, activeTheme.id, activeLanguage.id),
      status,
      themes: availableThemes.map((theme) => ({
        id: theme.id,
        name: theme.name,
        primary: theme.colors.primary,
        selected: theme.id === activeTheme.id,
      })),
    });
  }

  #normalizePreferences(
    preferences: UserPreferences,
    theme: string,
    language: UserPreferences["language"],
  ): UserPreferences {
    return {
      schema: "agent-devkit.user-preferences/v1",
      language,
      logRetentionDays: preferences.logRetentionDays,
      theme,
      updatedAt: preferences.updatedAt,
    };
  }
}
