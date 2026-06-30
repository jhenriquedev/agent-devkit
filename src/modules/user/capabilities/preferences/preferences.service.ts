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

    if (themes.isErr()) {
      return Result.fail(themes.unwrapError());
    }

    const availableThemes = themes.unwrap();
    const existing = await this.#repository.loadPreferences();

    if (existing.isErr()) {
      return Result.fail(existing.unwrapError());
    }

    let preferences = existing.unwrap();
    let status: PreferencesResult["status"] = "view";

    if (options.action === "set-theme") {
      if (options.theme === undefined) {
        return Result.fail(ErrorCodes.InvalidInput);
      }

      if (!availableThemes.some((theme) => theme.id === options.theme)) {
        return Result.fail(ErrorCodes.InvalidInput);
      }

      preferences = {
        schema: "agent-devkit.user-preferences/v1",
        theme: options.theme,
        updatedAt: new Date().toISOString(),
      };

      const save = await this.#repository.savePreferences(preferences);

      if (save.isErr()) {
        return Result.fail(save.unwrapError());
      }

      status = "updated";
    }

    const activeTheme =
      availableThemes.find((theme) => theme.id === preferences.theme) ?? availableThemes[0];

    if (activeTheme === undefined) {
      return Result.fail(ErrorCodes.AssetReadFailed);
    }

    return Result.ok({
      activeTheme,
      path: this.#repository.preferencesPath(),
      preferences: this.#normalizePreferences(preferences, activeTheme.id),
      status,
      themes: availableThemes.map((theme) => ({
        id: theme.id,
        name: theme.name,
        primary: theme.colors.primary,
        selected: theme.id === activeTheme.id,
      })),
    });
  }

  #normalizePreferences(preferences: UserPreferences, theme: string): UserPreferences {
    return {
      schema: "agent-devkit.user-preferences/v1",
      theme,
      updatedAt: preferences.updatedAt,
    };
  }
}
