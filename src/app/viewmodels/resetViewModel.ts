import type { ResetResult } from "../../domain/entities/ResetResult";

export function formatResetText(result: ResetResult): string {
  return [
    "Agent DevKit Reset  local state cleanup",
    "> agent reset",
    "",
    `[${result.status}] ${result.scope} state`,
    `  path    ${result.path}`,
    `  removed ${String(result.removed)}`,
  ].join("\n");
}
