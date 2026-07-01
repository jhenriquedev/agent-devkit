import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import type { Translator } from "../../../../infra/bases/i18n";
import type { DependenciesResult } from "./dependencies.entities";

const defaultTranslator = new I18nCatalog().translator("en-US");

export function formatDependenciesText(
  result: DependenciesResult,
  translator: Translator = defaultTranslator,
): string {
  const rows = [
    translator.t("dependencies.title"),
    translator.t("dependencies.command"),
    "",
    `[${result.action}] ${result.status}`,
  ];

  if (result.action === "list") {
    rows.push("", `  ${translator.t("dependencies.section.known")}`);
    rows.push(
      ...result.dependencies.map(
        (dependency) => `  ${dependency.id.padEnd(12)} ${dependency.name}`,
      ),
    );
    return rows.join("\n");
  }

  if ("checks" in result) {
    rows.push("", `  ${translator.t("dependencies.section.checks")}`);
    rows.push(
      ...result.checks.map(
        (check) => `  ${check.id.padEnd(12)} ${check.status.padEnd(14)} ${check.message}`,
      ),
    );
    return rows.join("\n");
  }

  if ("plan" in result) {
    rows.push("", `  ${translator.t("dependencies.section.plan")}`, `  ${result.plan.message}`);
    rows.push(
      ...result.plan.commands.map((command) => `  ${command.risk.padEnd(18)} ${command.command}`),
    );
    return rows.join("\n");
  }

  rows.push("", `  ${translator.t("dependencies.section.result")}`, `  ${result.result.message}`);
  return rows.join("\n");
}
