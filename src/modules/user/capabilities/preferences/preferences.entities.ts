import { z } from "zod";
import {
  type LanguageDefinition,
  LanguageDefinitionSchema,
  type LanguageId,
  type LanguageSummary,
} from "../../../../infra/bases/i18n";
import { type ThemeDefinition, ThemeDefinitionSchema } from "../../../../infra/bases/theme";

export const PreferencesServiceOptionsSchema = z
  .object({
    action: z.enum([
      "reset-defaults",
      "set-language",
      "set-log-retention",
      "set-theme",
      "update",
      "view",
    ]),
    language: z.enum(["pt-BR", "en-US", "fr-FR", "zh-CN", "ja-JP"]).optional(),
    logRetentionDays: z.number().int().min(1).max(3650).optional(),
    theme: z.string().min(1).optional(),
  })
  .strict();

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

export const PreferencesResultSchema = z.object({
  activeLanguage: LanguageDefinitionSchema.omit({ messages: true }),
  activeTheme: ThemeDefinitionSchema,
  languages: z.array(
    z.object({
      id: z.enum(["pt-BR", "en-US", "fr-FR", "zh-CN", "ja-JP"]),
      name: z.string().min(1),
      nativeName: z.string().min(1),
      selected: z.boolean(),
    }),
  ),
  path: z.string().min(1),
  preferences: z.object({
    schema: z.literal("agent-devkit.user-preferences/v1"),
    language: z.enum(["pt-BR", "en-US", "fr-FR", "zh-CN", "ja-JP"]),
    logRetentionDays: z.number().int().min(1).max(3650),
    theme: z.string().min(1),
    updatedAt: z.string().min(1),
  }),
  status: z.enum(["reset", "updated", "view"]),
  themes: z.array(
    z.object({
      id: z.string().min(1),
      name: z.string().min(1),
      primary: z.string().min(1),
      selected: z.boolean(),
    }),
  ),
});
