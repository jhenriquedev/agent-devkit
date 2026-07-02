import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import type { Translator } from "../../../../infra/bases/i18n";
import type { LogEvent, LogsAnalysisResult, LogsFileSummary } from "./analysis.entities";

const defaultTranslator = new I18nCatalog().translator("en-US");

function commandName(event: LogEvent): string {
  return event.category === "usage" ? event.command : (event.command ?? event.event);
}

function durationMs(event: LogEvent): number {
  return event.durationMs ?? 0;
}

function statusName(event: LogEvent): string {
  return event.category === "usage" ? event.status : event.level;
}

function formatEvent(event: LogEvent): string {
  return `${event.timestamp}  ${event.category.padEnd(9)} ${statusName(event).padEnd(9)} ${event.area.padEnd(7)} ${commandName(event)}  ${durationMs(event)}ms`;
}

function formatFiles(files: LogsFileSummary[]): string[] {
  return files.map(
    (file) =>
      `  ${file.date}  ${file.category.padEnd(9)} ${String(file.eventCount).padStart(4)} events  ${String(file.sizeBytes).padStart(6)} bytes`,
  );
}

function formatCounts(counts: Record<string, number>): string[] {
  return Object.entries(counts)
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .map(([key, count]) => `    ${key.padEnd(18)} ${count}`);
}

export function formatLogsAnalysisText(
  result: LogsAnalysisResult,
  translator: Translator = defaultTranslator,
): string {
  const t = (key: string, values?: Record<string, string | number>) => translator.t(key, values);
  const rows = [t("logs.title"), t("logs.command"), "", `[${result.action}] ${result.path}`];

  if (result.action === "list") {
    rows.push("", `  ${t("logs.section.files")}`);
    rows.push(...formatFiles(result.files));
    return rows.join("\n");
  }

  if (result.action === "read") {
    rows.push("", `  ${t("logs.section.events", { count: result.events.length })}`);
    rows.push(...result.events.map(formatEvent));
    rows.push(`  ${t("logs.totalEvents", { count: result.totalEvents })}`);
    return rows.join("\n");
  }

  if (result.action === "search") {
    rows.push(
      "",
      `  ${t("logs.section.matches", { count: result.totalMatches, query: result.query })}`,
    );
    rows.push(...result.events.map(formatEvent));
    return rows.join("\n");
  }

  rows.push(
    "",
    `  ${t("logs.totalEvents", { count: result.totalEvents })}`,
    `  ${t("logs.averageDuration", { duration: result.averageDurationMs })}`,
    "",
    `  ${t("logs.section.byCommand")}`,
    ...formatCounts(result.byCommand),
    "",
    `  ${t("logs.section.byCategory")}`,
    ...formatCounts(result.byCategory),
    "",
    `  ${t("logs.section.byArea")}`,
    ...formatCounts(result.byArea),
    "",
    `  ${t("logs.section.byStatus")}`,
    ...formatCounts(result.byStatus),
    "",
    `  ${t("logs.section.slowest")}`,
    ...result.slowest.map(formatEvent),
  );

  return rows.join("\n");
}
