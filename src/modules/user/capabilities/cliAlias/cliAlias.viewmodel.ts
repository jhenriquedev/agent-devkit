import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import type { Translator } from "../../../../infra/bases/i18n";
import type { CliAliasResult } from "./cliAlias.entities";

const defaultTranslator = new I18nCatalog().translator("en-US");

export function formatCliAliasText(
  result: CliAliasResult,
  translator: Translator = defaultTranslator,
): string {
  const t = (key: string, values?: Record<string, string | number | boolean>) =>
    translator.t(key, values);
  const lines = [t("alias.title")];

  if (result.alias === undefined) {
    lines.push(t("alias.status.notConfigured"));
  } else {
    lines.push(t("alias.line.name", { name: result.alias.name }));
    lines.push(t("alias.line.shim", { path: result.alias.shimPath }));
  }

  lines.push(t("alias.line.bin", { path: result.binDirectory }));

  if (!result.binDirectoryInPath) {
    lines.push(t("alias.line.activate", { command: result.activationCommand }));
  }

  return lines.join("\n");
}
