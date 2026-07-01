import { homedir } from "node:os";
import type { Command } from "commander";
import type { Translator } from "../../../infra/bases/i18n";
import type { LogsAnalysisOptions, LogsAnalysisResult } from "../../../modules/logs/logs.index";
import { createLogsModuleBindings, formatLogsAnalysisText } from "../../../modules/logs/logs.index";
import { logCategoryFromOptions, parseNonNegativeInteger, wantsJson } from "../command_options";
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
    .option("--all", options.translator.t("cli.logs.option.all"))
    .option("--technical", options.translator.t("cli.logs.option.technical"))
    .option("--json", options.translator.t("cli.logs.option.json"));

  logsCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "logs",
        options: () => logsCommand.opts(),
      },
      async (commandOptions: { all?: boolean; json?: boolean; technical?: boolean }) => {
        await printLogsResult(commandOptions, options.translator, {
          action: "list",
          category: logCategoryFromOptions(commandOptions),
        });
      },
    ),
  );

  const showCommand = logsCommand
    .command("show")
    .argument("[date]", options.translator.t("cli.logs.show.argument.date"))
    .description(options.translator.t("cli.logs.show.description"))
    .option("--all", options.translator.t("cli.logs.option.all"))
    .option("--json", options.translator.t("cli.logs.option.json"))
    .option("--limit <limit>", options.translator.t("cli.logs.option.limit"))
    .option("--technical", options.translator.t("cli.logs.option.technical"));

  showCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "logs.show",
        options: () => showCommand.opts(),
      },
      async (
        date: string | undefined,
        commandOptions: {
          all?: boolean;
          json?: boolean;
          limit?: string;
          technical?: boolean;
        },
      ) => {
        await printLogsResult(commandOptions, options.translator, {
          action: "read",
          category: logCategoryFromOptions(commandOptions),
          date,
          limit: parseNonNegativeInteger(commandOptions.limit),
        });
      },
    ),
  );

  const tailCommand = logsCommand
    .command("tail")
    .description(options.translator.t("cli.logs.tail.description"))
    .option("--all", options.translator.t("cli.logs.option.all"))
    .option("--date <date>", options.translator.t("cli.logs.option.date"))
    .option("--json", options.translator.t("cli.logs.option.json"))
    .option("--limit <limit>", options.translator.t("cli.logs.option.limit"))
    .option("--technical", options.translator.t("cli.logs.option.technical"));

  tailCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "logs.tail",
        options: () => tailCommand.opts(),
      },
      async (commandOptions: {
        all?: boolean;
        date?: string;
        json?: boolean;
        limit?: string;
        technical?: boolean;
      }) => {
        await printLogsResult(commandOptions, options.translator, {
          action: "read",
          category: logCategoryFromOptions(commandOptions),
          date: commandOptions.date,
          limit: parseNonNegativeInteger(commandOptions.limit),
          tail: true,
        });
      },
    ),
  );

  const searchCommand = logsCommand
    .command("search")
    .argument("<query>", options.translator.t("cli.logs.search.argument.query"))
    .description(options.translator.t("cli.logs.search.description"))
    .option("--all", options.translator.t("cli.logs.option.all"))
    .option("--date <date>", options.translator.t("cli.logs.option.date"))
    .option("--json", options.translator.t("cli.logs.option.json"))
    .option("--limit <limit>", options.translator.t("cli.logs.option.limit"))
    .option("--technical", options.translator.t("cli.logs.option.technical"));

  searchCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "logs.search",
        options: () => searchCommand.opts(),
      },
      async (
        query: string,
        commandOptions: {
          all?: boolean;
          date?: string;
          json?: boolean;
          limit?: string;
          technical?: boolean;
        },
      ) => {
        await printLogsResult(commandOptions, options.translator, {
          action: "search",
          category: logCategoryFromOptions(commandOptions),
          date: commandOptions.date,
          limit: parseNonNegativeInteger(commandOptions.limit),
          query,
        });
      },
    ),
  );

  const summaryCommand = logsCommand
    .command("summary")
    .description(options.translator.t("cli.logs.summary.description"))
    .option("--all", options.translator.t("cli.logs.option.all"))
    .option("--date <date>", options.translator.t("cli.logs.option.date"))
    .option("--json", options.translator.t("cli.logs.option.json"))
    .option("--technical", options.translator.t("cli.logs.option.technical"));

  summaryCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "logs.summary",
        options: () => summaryCommand.opts(),
      },
      async (commandOptions: {
        all?: boolean;
        date?: string;
        json?: boolean;
        technical?: boolean;
      }) => {
        await printLogsResult(commandOptions, options.translator, {
          action: "summary",
          category: logCategoryFromOptions(commandOptions),
          date: commandOptions.date,
        });
      },
    ),
  );
}
