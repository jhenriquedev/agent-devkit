import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type { Command } from "commander";
import { I18nCatalog } from "../../infra/assets/i18n_catalog";
import type { LanguageId, Translator } from "../../infra/bases/i18n";

const supportedLanguages: LanguageId[] = ["pt-BR", "en-US", "fr-FR", "zh-CN", "ja-JP"];

export type CliUserPreferences = {
  language: LanguageId;
  logRetentionDays: number;
};

function isLanguageId(value: unknown): value is LanguageId {
  return typeof value === "string" && supportedLanguages.includes(value as LanguageId);
}

function isLogRetentionDays(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 1 && value <= 3650;
}

export function loadCliUserPreferences(homeDirectory: string = homedir()): CliUserPreferences {
  const canonicalPreferencesPath = join(
    homeDirectory,
    ".agent-devkit",
    "data",
    "preferences",
    "preferences.json",
  );
  const legacyPreferencesPath = join(homeDirectory, ".agent-devkit", "preferences.json");
  const preferencesPath = existsSync(canonicalPreferencesPath)
    ? canonicalPreferencesPath
    : legacyPreferencesPath;

  if (!existsSync(preferencesPath)) {
    return { language: "pt-BR", logRetentionDays: 30 };
  }

  try {
    const payload = JSON.parse(readFileSync(preferencesPath, "utf8")) as {
      language?: unknown;
      logRetentionDays?: unknown;
    };

    return {
      language: isLanguageId(payload.language) ? payload.language : "pt-BR",
      logRetentionDays: isLogRetentionDays(payload.logRetentionDays)
        ? payload.logRetentionDays
        : 30,
    };
  } catch {
    return { language: "pt-BR", logRetentionDays: 30 };
  }
}

export function createCliTranslator(homeDirectory = homedir()): Translator {
  return new I18nCatalog().translator(loadCliUserPreferences(homeDirectory).language);
}

export function configureLocalizedHelp(program: Command, translator: Translator): void {
  const titleMap: Record<string, string> = {
    "Arguments:": "cli.help.title.arguments",
    "Commands:": "cli.help.title.commands",
    "Global Options:": "cli.help.title.globalOptions",
    "Options:": "cli.help.title.options",
    "Usage:": "cli.help.title.usage",
  };

  program.configureHelp({
    styleTitle: (title) => translator.t(titleMap[title] ?? title),
  });
  program.helpOption("-h, --help", translator.t("cli.help.option"));
}
