import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import type { Translator } from "../../../../infra/bases/i18n";
import type { SecretsVaultResult, SecretView } from "./vault.entities";

const defaultTranslator = new I18nCatalog().translator("en-US");

function formatSecret(secret: SecretView): string {
  return `  ${secret.name.padEnd(28)} ${(secret.service ?? "-").padEnd(12)} ${secret.value ?? "********"}`;
}

function formatAuditEvent(event: SecretsVaultResult & { action: "audit" }): string[] {
  return event.events.map(
    (auditEvent) =>
      `  ${auditEvent.timestamp.padEnd(24)} ${auditEvent.action.padEnd(8)} ${auditEvent.name.padEnd(28)} ${auditEvent.service ?? "-"}`,
  );
}

export function formatSecretsVaultText(
  result: SecretsVaultResult,
  translator: Translator = defaultTranslator,
): string {
  const t = (key: string, values?: Record<string, string | number | boolean>) =>
    translator.t(key, values);
  const rows = [t("secrets.title"), t("secrets.command"), "", `[${result.action}] ${result.path}`];

  if (result.action === "audit") {
    rows.push("", `  ${t("secrets.section.audit")}`, ...formatAuditEvent(result));
    return rows.join("\n");
  }

  if (result.action === "list") {
    rows.push("", `  ${t("secrets.section.items")}`, ...result.secrets.map(formatSecret));
    return rows.join("\n");
  }

  if (result.action === "remove") {
    rows.push(`  ${t("secrets.field.name").padEnd(8)} ${result.secret.name}`);
    rows.push(`  ${t("secrets.field.removed").padEnd(8)} ${String(result.removed)}`);
    return rows.join("\n");
  }

  rows.push(formatSecret(result.secret));
  return rows.join("\n");
}
