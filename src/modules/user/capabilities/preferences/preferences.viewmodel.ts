import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import type { Translator } from "../../../../infra/bases/i18n";
import type { PreferencesResult } from "./preferences.entities";

const fallbackTranslator = new I18nCatalog().translator("pt-BR");

export function formatPreferencesText(
  result: PreferencesResult,
  translator: Translator = fallbackTranslator,
): string {
  return [
    translator.t("preferences.title"),
    translator.t("preferences.command"),
    "",
    `[${translator.t("preferences.status", { status: result.status })}]`,
    `  ${translator.t("preferences.field.file").padEnd(8)} ${result.path}`,
    `  ${translator.t("preferences.field.theme").padEnd(8)} ${result.preferences.theme}`,
    `  ${translator.t("preferences.field.language").padEnd(8)} ${result.preferences.language}`,
    `  ${translator.t("preferences.field.logRetentionDays").padEnd(8)} ${result.preferences.logRetentionDays}d`,
    "",
    `  ${translator.t("preferences.section.themes")}`,
    ...result.themes.map(
      (theme) =>
        `    ${theme.selected ? "*" : " "} ${theme.id.padEnd(16)} ${theme.primary}  ${theme.name}`,
    ),
    "",
    `  ${translator.t("preferences.section.languages")}`,
    ...result.languages.map(
      (language) =>
        `    ${language.selected ? "*" : " "} ${language.id.padEnd(8)} ${language.nativeName}  ${language.name}`,
    ),
  ].join("\n");
}
