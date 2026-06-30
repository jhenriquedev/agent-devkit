import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import type { Translator } from "../../../../infra/bases/i18n";
import type { ProjectInitResult } from "./init.entities";

const defaultTranslator = new I18nCatalog().translator("en-US");

export function formatInitText(result: ProjectInitResult, translator?: Translator): string {
  const activeTranslator = translator ?? defaultTranslator;
  const t = (key: string) => activeTranslator.t(key);
  const rows = [
    t("init.title"),
    t("init.command"),
    "",
    `[${result.status}] ${t("init.projectState")}`,
    `  ${t("init.field.root").padEnd(7)} ${result.project.root}`,
  ];

  if (result.planned.length > 0) {
    rows.push(`  ${t("init.section.planned")}`);
    rows.push(...result.planned.map((file) => `    ${file}`));
  }

  if (result.created.length > 0) {
    rows.push(`  ${t("init.section.created")}`);
    rows.push(...result.created.map((file) => `    ${file}`));
  }

  if (result.skipped.length > 0) {
    rows.push(`  ${t("init.section.skipped")}`);
    rows.push(...result.skipped.map((file) => `    ${file}`));
  }

  return rows.join("\n");
}
