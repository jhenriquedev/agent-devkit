import type { Command } from "commander";
import type { Translator } from "../../../infra/bases/i18n";
import {
  type ContextMessageKind,
  type ContextMessageRole,
  type ContextSessionOrigin,
  type ContextSessionsOptions,
  type ContextSessionsResult,
  createContextModuleBindings,
  formatContextSessionsText,
} from "../../../modules/context/context.index";
import { parseNonNegativeInteger, wantsJson } from "../command_options";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterSessionsCommandOptions = {
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

type SessionStatusSelection = "active" | "archived" | "deleted" | "all";

function parseTags(value?: string): string[] | undefined {
  const tags = value
    ?.split(",")
    .map((tag) => tag.trim())
    .filter((tag) => tag.length > 0);

  return tags === undefined || tags.length === 0 ? undefined : tags;
}

function sessionsCapability() {
  const bindings = createContextModuleBindings();

  if (bindings.isErr()) {
    throw new Error(bindings.unwrapError());
  }

  return bindings.unwrap().capabilities.sessions;
}

async function printSessionsResult(
  commandOptions: { json?: boolean },
  options: ContextSessionsOptions,
): Promise<void> {
  const result = await sessionsCapability().execute(options);

  if (result.isErr()) {
    throw new Error(result.unwrapError());
  }

  const payload: ContextSessionsResult = result.unwrap();

  if (wantsJson(commandOptions)) {
    console.log(JSON.stringify(payload, null, 2));
    return;
  }

  console.log(formatContextSessionsText(payload));
}

export function registerSessionsCommand(
  program: Command,
  options: RegisterSessionsCommandOptions,
): void {
  const sessionsCommand = program
    .command("sessions")
    .alias("session")
    .description("list and manage Agent DevKit context sessions")
    .option("--json", "print session result as JSON")
    .option("--limit <limit>", "maximum number of sessions")
    .option("--project <projectId>", "project id")
    .option("--query <query>", "filter sessions by text")
    .option("--status <status>", "active, archived, deleted or all");

  sessionsCommand.action(
    options.usageLogging.track(
      { area: "user", command: "sessions", options: () => sessionsCommand.opts() },
      async (commandOptions: {
        json?: boolean;
        limit?: string;
        project?: string;
        query?: string;
        status?: SessionStatusSelection;
      }) => {
        await printSessionsResult(commandOptions, {
          action: "list",
          limit: parseNonNegativeInteger(commandOptions.limit),
          projectId: commandOptions.project,
          query: commandOptions.query,
          status: commandOptions.status,
        });
      },
    ),
  );

  const createCommand = sessionsCommand
    .command("create")
    .description("create a context session")
    .option("--json", "print session result as JSON")
    .option("--origin <origin>", "cli, tui, mcp or agent", "cli")
    .option("--project <projectId>", "project id")
    .option("--tags <tags>", "comma-separated tags")
    .option("--title <title>", "session title");

  createCommand.action(
    options.usageLogging.track(
      { area: "user", command: "sessions.create", options: () => createCommand.opts() },
      async (commandOptions: {
        json?: boolean;
        origin?: ContextSessionOrigin;
        project?: string;
        tags?: string;
        title?: string;
      }) => {
        await printSessionsResult(commandOptions, {
          action: "create",
          origin: commandOptions.origin ?? "cli",
          projectId: commandOptions.project,
          tags: parseTags(commandOptions.tags),
          title: commandOptions.title,
        });
      },
    ),
  );

  const appendCommand = sessionsCommand
    .command("append")
    .argument("<sessionId>", "session id")
    .description("append a message to a context session")
    .requiredOption("--content <content>", "message content")
    .option("--json", "print session result as JSON")
    .option("--kind <kind>", "message, event, tool-call, tool-result or summary", "message")
    .option("--role <role>", "user, assistant, system or tool", "user");

  appendCommand.action(
    options.usageLogging.track(
      { area: "user", command: "sessions.append", options: () => appendCommand.opts() },
      async (
        sessionId: string,
        commandOptions: {
          content: string;
          json?: boolean;
          kind?: ContextMessageKind;
          role?: ContextMessageRole;
        },
      ) => {
        await printSessionsResult(commandOptions, {
          action: "append-message",
          content: commandOptions.content,
          kind: commandOptions.kind ?? "message",
          role: commandOptions.role ?? "user",
          sessionId,
        });
      },
    ),
  );

  const showCommand = sessionsCommand
    .command("show")
    .argument("<sessionId>", "session id")
    .description("show a context session")
    .option("--json", "print session result as JSON")
    .option("--limit <limit>", "maximum number of messages")
    .option("--messages", "include messages");

  showCommand.action(
    options.usageLogging.track(
      { area: "user", command: "sessions.show", options: () => showCommand.opts() },
      async (
        sessionId: string,
        commandOptions: { json?: boolean; limit?: string; messages?: boolean },
      ) => {
        await printSessionsResult(commandOptions, {
          action: "show",
          includeMessages: commandOptions.messages === true,
          limit: parseNonNegativeInteger(commandOptions.limit),
          sessionId,
        });
      },
    ),
  );

  const searchCommand = sessionsCommand
    .command("search")
    .argument("<query>", "query")
    .description("search context sessions")
    .option("--json", "print session result as JSON")
    .option("--limit <limit>", "maximum number of results")
    .option("--project <projectId>", "project id");

  searchCommand.action(
    options.usageLogging.track(
      { area: "user", command: "sessions.search", options: () => searchCommand.opts() },
      async (
        query: string,
        commandOptions: { json?: boolean; limit?: string; project?: string },
      ) => {
        await printSessionsResult(commandOptions, {
          action: "search",
          limit: parseNonNegativeInteger(commandOptions.limit),
          projectId: commandOptions.project,
          query,
        });
      },
    ),
  );

  const resumeCommand = sessionsCommand
    .command("resume")
    .argument("<sessionId>", "session id")
    .description("resume a context session")
    .option("--json", "print session result as JSON");

  resumeCommand.action(
    options.usageLogging.track(
      { area: "user", command: "sessions.resume", options: () => resumeCommand.opts() },
      async (sessionId: string, commandOptions: { json?: boolean }) => {
        await printSessionsResult(commandOptions, { action: "resume", sessionId });
      },
    ),
  );

  const archiveCommand = sessionsCommand
    .command("archive")
    .argument("<sessionId>", "session id")
    .description("archive a context session")
    .option("--json", "print session result as JSON");

  archiveCommand.action(
    options.usageLogging.track(
      { area: "user", command: "sessions.archive", options: () => archiveCommand.opts() },
      async (sessionId: string, commandOptions: { json?: boolean }) => {
        await printSessionsResult(commandOptions, { action: "archive", sessionId });
      },
    ),
  );

  const deleteCommand = sessionsCommand
    .command("delete")
    .argument("<sessionId>", "session id")
    .description("delete a context session")
    .option("--hard", "remove session files")
    .option("--json", "print session result as JSON")
    .option("--yes", "confirm hard delete");

  deleteCommand.action(
    options.usageLogging.track(
      { area: "user", command: "sessions.delete", options: () => deleteCommand.opts() },
      async (
        sessionId: string,
        commandOptions: { hard?: boolean; json?: boolean; yes?: boolean },
      ) => {
        if (commandOptions.hard === true && commandOptions.yes !== true) {
          throw new Error("Hard delete requires --yes.");
        }

        await printSessionsResult(commandOptions, {
          action: "delete",
          hard: commandOptions.hard === true,
          sessionId,
        });
      },
    ),
  );
}
