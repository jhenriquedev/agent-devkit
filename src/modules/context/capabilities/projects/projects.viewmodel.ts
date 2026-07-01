import type { ContextProject, ContextProjectsResult } from "./projects.entities";

function projectLine(project: ContextProject): string {
  return `${project.id.padEnd(24)} ${project.status.padEnd(8)} ${project.name}`;
}

export function formatContextProjectsText(result: ContextProjectsResult): string {
  if (result.action === "list") {
    return ["Agent DevKit Projects", "", ...result.projects.map(projectLine)].join("\n");
  }

  if (result.action === "delete") {
    return `Agent DevKit Projects\n\n[delete] ${result.projectId} removed=${result.removed} hard=${result.hard}`;
  }

  return [
    "Agent DevKit Projects",
    "",
    `[${result.action}] ${result.project.id}`,
    projectLine(result.project),
  ].join("\n");
}
