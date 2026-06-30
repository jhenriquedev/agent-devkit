import { existsSync } from "node:fs";
import { access, mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import { type ThemeDefinition, ThemeDefinitionSchema } from "../../../../infra/bases/theme";
import type { UserPreferences } from "./preferences.entities";

export type PreferencesRepositoryOptions = {
  homeDirectory?: string;
  themesDirectory?: string;
};

export interface PreferencesRepositoryPort extends CapabilityRepositoryPort {
  loadPreferences(): Promise<Result<AgentDevKitErrorCode, UserPreferences>>;
  loadThemes(): Promise<Result<AgentDevKitErrorCode, ThemeDefinition[]>>;
  preferencesPath(): string;
  savePreferences(preferences: UserPreferences): Promise<Result<AgentDevKitErrorCode, void>>;
}

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

function defaultPreferences(): UserPreferences {
  return {
    schema: "agent-devkit.user-preferences/v1",
    theme: defaultTheme,
    updatedAt: new Date(0).toISOString(),
  };
}

export class PreferencesRepository implements PreferencesRepositoryPort {
  readonly repositoryId = "user.preferences.repository";
  readonly #homeDirectory: string;
  readonly #themesDirectory: string;

  constructor(options: PreferencesRepositoryOptions = {}) {
    this.#homeDirectory = options.homeDirectory ?? homedir();
    this.#themesDirectory = options.themesDirectory ?? defaultThemesDirectory();
  }

  async loadPreferences(): Promise<Result<AgentDevKitErrorCode, UserPreferences>> {
    try {
      await access(this.preferencesPath());
    } catch {
      return Result.ok(defaultPreferences());
    }

    try {
      const payload = JSON.parse(await readFile(this.preferencesPath(), "utf8")) as UserPreferences;

      if (payload.schema !== "agent-devkit.user-preferences/v1") {
        return Result.fail(ErrorCodes.InvalidInput);
      }

      return Result.ok(payload);
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }
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
    return join(this.#homeDirectory, ".agent-devkit", "preferences.json");
  }

  async savePreferences(preferences: UserPreferences): Promise<Result<AgentDevKitErrorCode, void>> {
    try {
      await mkdir(dirname(this.preferencesPath()), { recursive: true });
      await writeFile(this.preferencesPath(), `${JSON.stringify(preferences, null, 2)}\n`);
      return Result.ok(undefined);
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }
}
