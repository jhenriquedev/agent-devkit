import type { ThemeDefinition } from "../../../../infra/bases/theme";

export type UserPreferences = {
  schema: "agent-devkit.user-preferences/v1";
  theme: string;
  updatedAt: string;
};

export type ThemeSummary = {
  id: string;
  name: string;
  primary: string;
  selected: boolean;
};

export type PreferencesStatus = "updated" | "view";

export type PreferencesResult = {
  activeTheme: ThemeDefinition;
  path: string;
  preferences: UserPreferences;
  status: PreferencesStatus;
  themes: ThemeSummary[];
};

export type PreferencesServiceOptions = {
  action: "set-theme" | "view";
  theme?: string;
};
