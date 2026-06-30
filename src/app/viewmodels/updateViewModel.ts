import type { SelfUpdateResult } from "../../domain/entities/SelfUpdateResult";

export function formatUpdateText(result: SelfUpdateResult): string {
  return [
    "Agent DevKit Update  npm versions",
    "> agent update",
    "",
    `[${result.status}] ${result.packageName}`,
    `  current  ${result.currentVersion}`,
    `  selected ${result.selectedVersion}`,
    result.command ? `  command  ${result.command}` : "  command  no update required",
    "",
    "  versions",
    ...result.versions.slice(0, 8).map((version) => {
      const marker = version.selected ? ">" : " ";
      const labels = [
        version.current ? "current" : undefined,
        version.latest ? "latest" : undefined,
      ]
        .filter(Boolean)
        .join(", ");
      return `  ${marker} ${version.version}${labels ? `  ${labels}` : ""}`;
    }),
  ].join("\n");
}
