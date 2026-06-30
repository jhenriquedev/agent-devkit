import type { LanguageDefinition, LanguageId, LanguageSummary } from "../../../../infra/bases/i18n";
import type { ThemeDefinition } from "../../../../infra/bases/theme";

export type UserPreferences = {
  schema: "agent-devkit.user-preferences/v1";
  language: LanguageId;
  logRetentionDays: number;
  theme: string;
  updatedAt: string;
};

export type ThemeSummary = {
  id: string;
  name: string;
  primary: string;
  selected: boolean;
};

export type PreferencesStatus = "reset" | "updated" | "view";

export type PreferencesResult = {
  activeLanguage: LanguageDefinition;
  activeTheme: ThemeDefinition;
  languages: LanguageSummary[];
  path: string;
  preferences: UserPreferences;
  status: PreferencesStatus;
  themes: ThemeSummary[];
};

export type PreferencesServiceOptions = {
  action: "reset-defaults" | "set-language" | "set-log-retention" | "set-theme" | "update" | "view";
  language?: LanguageId;
  logRetentionDays?: number;
  theme?: string;
};
