import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import type { Translator } from "../../../../infra/bases/i18n";
import type { SelfUpdateResult } from "./update.entities";

const defaultTranslator = new I18nCatalog().translator("en-US");

export function formatUpdateText(result: SelfUpdateResult, translator?: Translator): string {
  const activeTranslator = translator ?? defaultTranslator;
  const t = (key: string) => activeTranslator.t(key);

  return [
    t("update.title"),
    t("update.command"),
    "",
    `[${result.status}] ${result.packageName}`,
    `  ${t("update.field.current").padEnd(8)} ${result.currentVersion}`,
    `  ${t("update.field.selected").padEnd(8)} ${result.selectedVersion}`,
    result.command
      ? `  ${t("update.field.command").padEnd(8)} ${result.command}`
      : `  ${t("update.field.command").padEnd(8)} ${t("update.noUpdateRequired")}`,
    "",
    `  ${t("update.section.versions")}`,
    ...result.versions.slice(0, 8).map((version) => {
      const marker = version.selected ? ">" : " ";
      const labels = [
        version.current ? t("update.label.current") : undefined,
        version.latest ? t("update.label.latest") : undefined,
      ]
        .filter(Boolean)
        .join(", ");
      return `  ${marker} ${version.version}${labels ? `  ${labels}` : ""}`;
    }),
  ].join("\n");
}
