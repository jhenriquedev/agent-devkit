import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import type { Translator } from "../../../../infra/bases/i18n";
import type { ModelsRegistryResult, ModelView } from "./registry.entities";

const defaultTranslator = new I18nCatalog().translator("en-US");

function formatSize(bytes: number): string {
  if (bytes <= 0) {
    return "-";
  }

  const megabytes = bytes / 1_000_000;
  return megabytes >= 1000 ? `${(megabytes / 1000).toFixed(1)}GB` : `${Math.round(megabytes)}MB`;
}

function formatModel(model: ModelView): string {
  const installedMark = model.installed ? "*" : " ";
  const defaultMark = model.isDefault ? "D" : " ";
  const state = model.installed ? "installed" : "available";

  return `  ${installedMark}${defaultMark} ${model.id.padEnd(32)} ${model.parameters.padEnd(6)} ${model.quantization.padEnd(8)} ${formatSize(model.sizeBytes).padEnd(7)} ${state}`;
}

export function formatModelsRegistryText(
  result: ModelsRegistryResult,
  translator: Translator = defaultTranslator,
): string {
  const t = (key: string, values?: Record<string, string | number | boolean>) =>
    translator.t(key, values);
  const rows = [
    t("models.title"),
    t("models.command"),
    "",
    `[${result.action}] ${result.directory}`,
  ];

  if (result.action === "list" || result.action === "status" || result.action === "update") {
    if (result.action === "list" && result.defaultId !== undefined) {
      rows.push(`  ${t("models.field.default")} ${result.defaultId}`);
    }

    rows.push("", ...result.models.map(formatModel));
    return rows.join("\n");
  }

  if (result.action === "install") {
    rows.push(formatModel(result.model));
    return rows.join("\n");
  }

  if (result.action === "uninstall") {
    rows.push(`  ${result.id} ${result.removed ? "removed" : "not found"}`);
    return rows.join("\n");
  }

  const roleSuffix = result.role === undefined ? "" : ` (${result.role})`;
  rows.push(`  ${t("models.field.default")} ${result.defaultId}${roleSuffix}`);
  return rows.join("\n");
}
