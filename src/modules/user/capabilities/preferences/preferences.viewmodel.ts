import type { Translator } from "../../../../infra/bases/i18n";
import type { PreferencesResult } from "./preferences.entities";

const fallbackTranslator: Translator = {
  language: "pt-BR",
  t: (key, values = {}) => {
    const fallback: Record<string, string> = {
      "preferences.command": "> agent preferences",
      "preferences.field.file": "arquivo",
      "preferences.field.language": "idioma",
      "preferences.field.logRetentionDays": "retencao",
      "preferences.field.theme": "tema",
      "preferences.section.languages": "idiomas",
      "preferences.section.themes": "temas",
      "preferences.status": "{{status}} preferencias do usuario",
      "preferences.title": "Preferencias do Agent DevKit",
    };
    return (fallback[key] ?? key).replaceAll(/\{\{([a-zA-Z0-9_.-]+)\}\}/g, (_, name: string) =>
      values[name] === undefined ? `{{${name}}}` : String(values[name]),
    );
  },
};

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
