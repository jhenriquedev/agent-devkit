import { homedir } from "node:os";
import type { Command } from "commander";
import type { Translator } from "../../../infra/bases/i18n";
import {
  type ContextProjectsOptions,
  type ContextProjectsResult,
  createContextModuleBindings,
  formatContextProjectsText,
} from "../../../modules/context/context.index";
import { wantsJson } from "../command_options";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterProjectsCommandOptions = {
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

type ProjectStatusSelection = "active" | "archived" | "deleted" | "all";

function parseTags(value?: string): string[] | undefined {
  const tags = value
    ?.split(",")
    .map((tag) => tag.trim())
    .filter((tag) => tag.length > 0);

  return tags === undefined || tags.length === 0 ? undefined : tags;
}

function projectsCapability() {
  const bindings = createContextModuleBindings();

  if (bindings.isErr()) {
    throw new Error(bindings.unwrapError());
  }

  return bindings.unwrap().capabilities.projects;
}

async function printProjectsResult(
  commandOptions: { json?: boolean },
  options: ContextProjectsOptions,
): Promise<void> {
  const result = await projectsCapability().execute(options);

  if (result.isErr()) {
    throw new Error(result.unwrapError());
  }

  const payload: ContextProjectsResult = result.unwrap();

  if (wantsJson(commandOptions)) {
    console.log(JSON.stringify(payload, null, 2));
    return;
  }

  console.log(formatContextProjectsText(payload));
}

export function registerProjectsCommand(
  program: Command,
  options: RegisterProjectsCommandOptions,
): void {
  const projectsCommand = program
    .command("projects")
    .alias("project")
    .description("list and manage Agent DevKit context projects")
    .option("--json", "print project result as JSON")
    .option("--query <query>", "filter projects by text")
    .option("--status <status>", "active, archived, deleted or all");

  projectsCommand.action(
    options.usageLogging.track(
      {
        area: "user",
        command: "projects",
        options: () => projectsCommand.opts(),
      },
      async (commandOptions: {
        json?: boolean;
        query?: string;
        status?: ProjectStatusSelection;
      }) => {
        await printProjectsResult(commandOptions, {
          action: "list",
          query: commandOptions.query,
          status: commandOptions.status,
        });
      },
    ),
  );

  const createCommand = projectsCommand
    .command("create")
    .description("create a context project")
    .requiredOption("--name <name>", "project name")
    .option("--description <description>", "project description")
    .option("--json", "print project result as JSON")
    .option("--path <path>", "project path")
    .option("--tags <tags>", "comma-separated tags");

  createCommand.action(
    options.usageLogging.track(
      {
        area: "user",
        command: "projects.create",
        options: () => createCommand.opts(),
      },
      async (commandOptions: {
        description?: string;
        json?: boolean;
        name: string;
        path?: string;
        tags?: string;
      }) => {
        await printProjectsResult(commandOptions, {
          action: "create",
          description: commandOptions.description,
          metadata: { homeDirectory: homedir() },
          name: commandOptions.name,
          path: commandOptions.path,
          tags: parseTags(commandOptions.tags),
        });
      },
    ),
  );

  const showCommand = projectsCommand
    .command("show")
    .argument("<projectId>", "project id")
    .description("show a context project")
    .option("--json", "print project result as JSON");

  showCommand.action(
    options.usageLogging.track(
      { area: "user", command: "projects.show", options: () => showCommand.opts() },
      async (projectId: string, commandOptions: { json?: boolean }) => {
        await printProjectsResult(commandOptions, { action: "show", projectId });
      },
    ),
  );

  const updateCommand = projectsCommand
    .command("update")
    .argument("<projectId>", "project id")
    .description("update a context project")
    .option("--description <description>", "project description")
    .option("--json", "print project result as JSON")
    .option("--name <name>", "project name")
    .option("--path <path>", "project path")
    .option("--tags <tags>", "comma-separated tags");

  updateCommand.action(
    options.usageLogging.track(
      { area: "user", command: "projects.update", options: () => updateCommand.opts() },
      async (
        projectId: string,
        commandOptions: {
          description?: string;
          json?: boolean;
          name?: string;
          path?: string;
          tags?: string;
        },
      ) => {
        await printProjectsResult(commandOptions, {
          action: "update",
          description: commandOptions.description,
          name: commandOptions.name,
          path: commandOptions.path,
          projectId,
          tags: parseTags(commandOptions.tags),
        });
      },
    ),
  );

  const archiveCommand = projectsCommand
    .command("archive")
    .argument("<projectId>", "project id")
    .description("archive a context project")
    .option("--json", "print project result as JSON");

  archiveCommand.action(
    options.usageLogging.track(
      { area: "user", command: "projects.archive", options: () => archiveCommand.opts() },
      async (projectId: string, commandOptions: { json?: boolean }) => {
        await printProjectsResult(commandOptions, { action: "archive", projectId });
      },
    ),
  );

  const deleteCommand = projectsCommand
    .command("delete")
    .argument("<projectId>", "project id")
    .description("delete a context project")
    .option("--hard", "remove project files")
    .option("--json", "print project result as JSON")
    .option("--yes", "confirm hard delete");

  deleteCommand.action(
    options.usageLogging.track(
      { area: "user", command: "projects.delete", options: () => deleteCommand.opts() },
      async (
        projectId: string,
        commandOptions: { hard?: boolean; json?: boolean; yes?: boolean },
      ) => {
        if (commandOptions.hard === true && commandOptions.yes !== true) {
          throw new Error("Hard delete requires --yes.");
        }

        await printProjectsResult(commandOptions, {
          action: "delete",
          hard: commandOptions.hard === true,
          projectId,
        });
      },
    ),
  );
}
