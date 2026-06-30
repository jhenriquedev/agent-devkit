import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import type { Translator } from "../../../../infra/bases/i18n";
import type { ResetResult } from "./reset.entities";

const defaultTranslator = new I18nCatalog().translator("en-US");

export function formatResetText(result: ResetResult, translator?: Translator): string {
  const activeTranslator = translator ?? defaultTranslator;
  const t = (key: string, values?: Record<string, string>) => activeTranslator.t(key, values);
  const scope = t(`reset.scope.${result.scope}`);

  return [
    t("reset.title"),
    t("reset.command"),
    "",
    `[${result.status}] ${t("reset.state", { scope })}`,
    `  ${t("reset.field.path").padEnd(7)} ${result.path}`,
    `  ${t("reset.field.removed").padEnd(7)} ${String(result.removed)}`,
  ].join("\n");
}
