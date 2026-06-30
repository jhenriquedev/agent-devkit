import type { ProjectInitResult } from "./init.entities";

export function formatInitText(result: ProjectInitResult): string {
  const rows = [
    "Agent DevKit Init  local project state",
    "> agent init",
    "",
    `[${result.status}] project state`,
    `  root    ${result.project.root}`,
  ];

  if (result.planned.length > 0) {
    rows.push("  planned");
    rows.push(...result.planned.map((file) => `    ${file}`));
  }

  if (result.created.length > 0) {
    rows.push("  created");
    rows.push(...result.created.map((file) => `    ${file}`));
  }

  if (result.skipped.length > 0) {
    rows.push("  skipped");
    rows.push(...result.skipped.map((file) => `    ${file}`));
  }

  return rows.join("\n");
}
