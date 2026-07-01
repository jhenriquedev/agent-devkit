import type { ContextSessionIndex, ContextSessionsResult } from "./sessions.entities";

function sessionLine(session: ContextSessionIndex): string {
  return `${session.sessionId.padEnd(32)} ${session.status.padEnd(8)} ${session.title}`;
}

export function formatContextSessionsText(result: ContextSessionsResult): string {
  if (result.action === "list") {
    return ["Agent DevKit Sessions", "", ...result.sessions.map(sessionLine)].join("\n");
  }

  if (result.action === "search") {
    return [
      "Agent DevKit Sessions",
      "",
      `[search] ${result.query}`,
      ...result.results.map((session) => `${sessionLine(session)} score=${session.score}`),
    ].join("\n");
  }

  if (result.action === "delete") {
    return `Agent DevKit Sessions\n\n[delete] ${result.sessionId} removed=${result.removed} hard=${result.hard}`;
  }

  const session = "index" in result ? result.index : undefined;
  const id = "session" in result ? result.session.id : session?.sessionId;

  return ["Agent DevKit Sessions", "", `[${result.action}] ${id ?? ""}`].join("\n");
}
