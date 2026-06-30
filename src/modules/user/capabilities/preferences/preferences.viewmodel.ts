import type { PreferencesResult } from "./preferences.entities";

export function formatPreferencesText(result: PreferencesResult): string {
  return [
    "Agent DevKit Preferences",
    "> agent preferences",
    "",
    `[${result.status}] user preferences`,
    `  file   ${result.path}`,
    `  theme  ${result.preferences.theme}`,
    "",
    "  themes",
    ...result.themes.map(
      (theme) =>
        `    ${theme.selected ? "*" : " "} ${theme.id.padEnd(16)} ${theme.primary}  ${theme.name}`,
    ),
  ].join("\n");
}
