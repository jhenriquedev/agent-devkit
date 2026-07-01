import type { Command } from "commander";
import type { Translator } from "../../../infra/bases/i18n";
import type { ToolRuntimeResult } from "../../../infra/bases/tool_runtime";
import { formatDependenciesText } from "../../../modules/environment/environment.index";
import { wantsJson } from "../command_options";
import { createCliToolRuntime } from "../toolRuntime";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterInstallCommandOptions = {
  currentVersion: string;
  packageName: string;
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

type InstallCommandOptions = {
  dryRun?: boolean;
  json?: boolean;
  node?: boolean;
  verify?: boolean;
  yes?: boolean;
};

function selectedDependency(
  dependency: string | undefined,
  options: InstallCommandOptions,
): string {
  if (options.node === true) {
    return "node";
  }

  if (dependency !== undefined && dependency.trim().length > 0) {
    return dependency.trim();
  }

  throw new Error("Expected a dependency id.");
}

function runtime(options: RegisterInstallCommandOptions) {
  return createCliToolRuntime({
    currentVersion: options.currentVersion,
    packageName: options.packageName,
  });
}

function dependencyAction(options: InstallCommandOptions): "install" | "plan-install" | "verify" {
  if (options.verify === true) {
    return "verify";
  }

  return options.yes === true && options.dryRun !== true ? "install" : "plan-install";
}

function printResult(result: ToolRuntimeResult, translator: Translator, json: boolean): void {
  if (json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  if (result.status !== "succeeded") {
    console.error(JSON.stringify(result, null, 2));
    return;
  }

  console.log(formatDependenciesText(result.output as never, translator));
}

export function registerInstallCommand(
  program: Command,
  options: RegisterInstallCommandOptions,
): void {
  const installCommand = program
    .command("install")
    .argument("[dependency]", options.translator.t("cli.install.argument.dependency"))
    .description(options.translator.t("cli.install.description"))
    .option("--dry-run", options.translator.t("cli.install.option.dryRun"))
    .option("--json", options.translator.t("cli.install.option.json"))
    .option("--node", options.translator.t("cli.install.option.node"))
    .option("--verify", options.translator.t("cli.install.option.verify"))
    .option("--yes", options.translator.t("cli.install.option.yes"));

  installCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "install",
        options: () => installCommand.opts(),
      },
      async (dependency: string | undefined, commandOptions: InstallCommandOptions) => {
        const id = selectedDependency(dependency, commandOptions);
        const action = dependencyAction(commandOptions);
        const result = await runtime(options).execute({
          approved: commandOptions.yes === true,
          capabilityId: "environment.dependencies",
          input: {
            action,
            confirmed: commandOptions.yes === true,
            dependency: id,
          },
          interface: "cli",
          requestedBy: "agent.install",
        });

        printResult(result, options.translator, wantsJson(commandOptions));

        if (result.status !== "succeeded") {
          process.exitCode = 1;
        }
      },
    ),
  );
}
