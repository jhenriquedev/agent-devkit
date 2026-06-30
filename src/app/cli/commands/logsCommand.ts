import { homedir } from "node:os";
import type { Command } from "commander";
import type { Translator } from "../../../infra/bases/i18n";
import type { LogsAnalysisOptions, LogsAnalysisResult } from "../../../modules/logs/logs.index";
import { createLogsModuleBindings, formatLogsAnalysisText } from "../../../modules/logs/logs.index";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterLogsCommandOptions = {
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

function logsCapability() {
  const bindings = createLogsModuleBindings({ homeDirectory: homedir() });

  if (bindings.isErr()) {
    throw new Error(bindings.unwrapError());
  }

  return bindings.unwrap().capabilities.analysis;
}

function wantsJson(options?: { json?: boolean }): boolean {
  return options?.json === true || process.argv.includes("--json");
}

function parseLimit(value?: string): number | undefined {
  if (value === undefined) {
    return undefined;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined;
}

async function printLogsResult(
  commandOptions: { json?: boolean },
  translator: Translator,
  options: LogsAnalysisOptions,
): Promise<void> {
  const result = await logsCapability().execute(options);

  if (result.isErr()) {
    throw new Error(result.unwrapError());
  }

  const payload: LogsAnalysisResult = result.unwrap();

  if (wantsJson(commandOptions)) {
    console.log(JSON.stringify(payload, null, 2));
    return;
  }

  console.log(formatLogsAnalysisText(payload, translator));
}

export function registerLogsCommand(program: Command, options: RegisterLogsCommandOptions): void {
  const logsCommand = program
    .command("logs")
    .description(options.translator.t("cli.logs.description"))
    .option("--json", options.translator.t("cli.logs.option.json"));

  logsCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "logs",
        options: () => logsCommand.opts(),
      },
      async (commandOptions: { json?: boolean }) => {
        await printLogsResult(commandOptions, options.translator, { action: "list" });
      },
    ),
  );

  const showCommand = logsCommand
    .command("show")
    .argument("[date]", options.translator.t("cli.logs.show.argument.date"))
    .description(options.translator.t("cli.logs.show.description"))
    .option("--json", options.translator.t("cli.logs.option.json"))
    .option("--limit <limit>", options.translator.t("cli.logs.option.limit"));

  showCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "logs.show",
        options: () => showCommand.opts(),
      },
      async (date: string | undefined) => {
        const commandOptions = showCommand.opts<{ json?: boolean; limit?: string }>();
        await printLogsResult(commandOptions, options.translator, {
          action: "read",
          date,
          limit: parseLimit(commandOptions.limit),
        });
      },
    ),
  );

  const tailCommand = logsCommand
    .command("tail")
    .description(options.translator.t("cli.logs.tail.description"))
    .option("--date <date>", options.translator.t("cli.logs.option.date"))
    .option("--json", options.translator.t("cli.logs.option.json"))
    .option("--limit <limit>", options.translator.t("cli.logs.option.limit"));

  tailCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "logs.tail",
        options: () => tailCommand.opts(),
      },
      async () => {
        const commandOptions = tailCommand.opts<{
          date?: string;
          json?: boolean;
          limit?: string;
        }>();
        await printLogsResult(commandOptions, options.translator, {
          action: "read",
          date: commandOptions.date,
          limit: parseLimit(commandOptions.limit),
          tail: true,
        });
      },
    ),
  );

  const searchCommand = logsCommand
    .command("search")
    .argument("<query>", options.translator.t("cli.logs.search.argument.query"))
    .description(options.translator.t("cli.logs.search.description"))
    .option("--date <date>", options.translator.t("cli.logs.option.date"))
    .option("--json", options.translator.t("cli.logs.option.json"))
    .option("--limit <limit>", options.translator.t("cli.logs.option.limit"));

  searchCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "logs.search",
        options: () => searchCommand.opts(),
      },
      async (query: string) => {
        const commandOptions = searchCommand.opts<{
          date?: string;
          json?: boolean;
          limit?: string;
        }>();
        await printLogsResult(commandOptions, options.translator, {
          action: "search",
          date: commandOptions.date,
          limit: parseLimit(commandOptions.limit),
          query,
        });
      },
    ),
  );

  const summaryCommand = logsCommand
    .command("summary")
    .description(options.translator.t("cli.logs.summary.description"))
    .option("--date <date>", options.translator.t("cli.logs.option.date"))
    .option("--json", options.translator.t("cli.logs.option.json"));

  summaryCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "logs.summary",
        options: () => summaryCommand.opts(),
      },
      async () => {
        const commandOptions = summaryCommand.opts<{ date?: string; json?: boolean }>();
        await printLogsResult(commandOptions, options.translator, {
          action: "summary",
          date: commandOptions.date,
        });
      },
    ),
  );
}
