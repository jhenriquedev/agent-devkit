import { z } from "zod";

export const LanguageDefinitionSchema = z.object({
  schema: z.literal("agent-devkit.i18n/v1"),
  id: z.enum(["pt-BR", "en-US", "fr-FR", "zh-CN", "ja-JP"]),
  name: z.string().min(1),
  nativeName: z.string().min(1),
  messages: z.record(z.string().min(1), z.string()),
});

export type LanguageDefinition = z.infer<typeof LanguageDefinitionSchema>;
export type LanguageId = LanguageDefinition["id"];

export type LanguageSummary = {
  id: LanguageId;
  name: string;
  nativeName: string;
  selected: boolean;
};

export interface Translator {
  language: LanguageId;
  t(key: string, values?: Record<string, string | number | boolean>): string;
}
