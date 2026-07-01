import type { Command } from "commander";
import type { Translator } from "../../../infra/bases/i18n";
import type { ToolRuntimeResult } from "../../../infra/bases/tool_runtime";
import { createCliToolRuntime } from "../toolRuntime";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterRunCommandOptions = {
  currentVersion: string;
  packageName: string;
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

function parseJsonInput(input: string): unknown {
  try {
    return JSON.parse(input);
  } catch {
    throw new Error("Invalid JSON passed to --input.");
  }
}

function formatRunText(result: ToolRuntimeResult): string {
  if (result.status === "succeeded") {
    return JSON.stringify(result.output, null, 2);
  }

  return [`${result.status}: ${result.capabilityId}`, result.error?.message, result.error?.hint]
    .filter((line) => line !== undefined && line.length > 0)
    .join("\n");
}

export function registerRunCommand(program: Command, options: RegisterRunCommandOptions): void {
  const runCommand = program
    .command("run")
    .argument("<capabilityId>", options.translator.t("cli.run.argument.capabilityId"))
    .description(options.translator.t("cli.run.description"))
    .requiredOption("--input <json>", options.translator.t("cli.run.option.input"))
    .option("--approve", options.translator.t("cli.run.option.approve"))
    .option("--json", options.translator.t("cli.run.option.json"));

  runCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "run",
        options: () => runCommand.opts(),
        redactOptions: ["--input"],
      },
      async (
        capabilityId: string,
        commandOptions: { approve?: boolean; input: string; json?: boolean },
      ) => {
        const runtime = createCliToolRuntime({
          currentVersion: options.currentVersion,
          packageName: options.packageName,
        });
        const result = await runtime.execute({
          approved: commandOptions.approve === true,
          capabilityId,
          input: parseJsonInput(commandOptions.input),
          interface: "cli",
          requestedBy: "agent.run",
        });

        if (commandOptions.json === true) {
          console.log(JSON.stringify(result, null, 2));
        } else if (result.status === "succeeded") {
          console.log(formatRunText(result));
        } else {
          console.error(formatRunText(result));
        }

        if (result.status !== "succeeded") {
          process.exitCode = 1;
        }
      },
    ),
  );
}
