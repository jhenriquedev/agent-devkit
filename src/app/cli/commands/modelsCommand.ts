import { homedir } from "node:os";
import type { Command } from "commander";
import type { AgentDevKitErrorCode } from "../../../infra/bases/errors";
import type { Translator } from "../../../infra/bases/i18n";
import type { Result } from "../../../infra/bases/result";
import type { ModelsRegistryResult } from "../../../modules/models/models.index";
import {
  createModelsModuleBindings,
  formatModelsRegistryText,
} from "../../../modules/models/models.index";
import { wantsJson } from "../command_options";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterModelsCommandOptions = {
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

function modelsCapability() {
  const bindings = createModelsModuleBindings({ homeDirectory: homedir() });

  if (bindings.isErr()) {
    throw new Error(bindings.unwrapError());
  }

  return bindings.unwrap().capabilities.registry;
}

function printResult(
  result: Result<AgentDevKitErrorCode, ModelsRegistryResult>,
  translator: Translator,
  json?: boolean,
): void {
  if (result.isErr()) {
    throw new Error(result.unwrapError());
  }

  const payload = result.unwrap();

  if (json === true) {
    console.log(JSON.stringify(payload, null, 2));
    return;
  }

  console.log(formatModelsRegistryText(payload, translator));
}

export function registerModelsCommand(
  program: Command,
  options: RegisterModelsCommandOptions,
): void {
  const modelsCommand = program
    .command("models")
    .description(options.translator.t("cli.models.description"))
    .option("--json", options.translator.t("cli.models.option.json"));

  modelsCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "models",
        createStateIfMissing: false,
        options: () => modelsCommand.opts(),
      },
      async (commandOptions: { json?: boolean }) => {
        printResult(
          await modelsCapability().execute({ action: "list" }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const listCommand = modelsCommand
    .command("list")
    .description(options.translator.t("cli.models.list.description"))
    .option("--json", options.translator.t("cli.models.option.json"));

  listCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "models.list",
        createStateIfMissing: false,
        options: () => listCommand.opts(),
      },
      async (commandOptions: { json?: boolean }) => {
        printResult(
          await modelsCapability().execute({ action: "list" }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const statusCommand = modelsCommand
    .command("status")
    .argument("[id]", options.translator.t("cli.models.argument.id"))
    .description(options.translator.t("cli.models.status.description"))
    .option("--json", options.translator.t("cli.models.option.json"));

  statusCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "models.status",
        createStateIfMissing: false,
        options: () => statusCommand.opts(),
      },
      async (id: string | undefined) => {
        const commandOptions = statusCommand.opts<{ json?: boolean }>();
        printResult(
          await modelsCapability().execute({ action: "status", id }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const installCommand = modelsCommand
    .command("install")
    .argument("<id>", options.translator.t("cli.models.argument.id"))
    .description(options.translator.t("cli.models.install.description"))
    .option("--json", options.translator.t("cli.models.option.json"));

  installCommand.action(
    options.usageLogging.track(
      { area: "system", command: "models.install", options: () => installCommand.opts() },
      async (id: string) => {
        const commandOptions = installCommand.opts<{ json?: boolean }>();

        if (wantsJson(commandOptions) !== true) {
          process.stderr.write(`${options.translator.t("cli.models.install.progress", { id })}\n`);
        }

        printResult(
          await modelsCapability().execute({ action: "install", id }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const uninstallCommand = modelsCommand
    .command("uninstall")
    .alias("rm")
    .argument("<id>", options.translator.t("cli.models.argument.id"))
    .description(options.translator.t("cli.models.uninstall.description"))
    .option("--json", options.translator.t("cli.models.option.json"));

  uninstallCommand.action(
    options.usageLogging.track(
      { area: "system", command: "models.uninstall", options: () => uninstallCommand.opts() },
      async (id: string) => {
        const commandOptions = uninstallCommand.opts<{ json?: boolean }>();
        printResult(
          await modelsCapability().execute({ action: "uninstall", id }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const updateCommand = modelsCommand
    .command("update")
    .argument("[id]", options.translator.t("cli.models.argument.id"))
    .description(options.translator.t("cli.models.update.description"))
    .option("--json", options.translator.t("cli.models.option.json"));

  updateCommand.action(
    options.usageLogging.track(
      { area: "system", command: "models.update", options: () => updateCommand.opts() },
      async (id: string | undefined) => {
        const commandOptions = updateCommand.opts<{ json?: boolean }>();
        printResult(
          await modelsCapability().execute({ action: "update", id }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const useCommand = modelsCommand
    .command("use")
    .argument("<id>", options.translator.t("cli.models.argument.id"))
    .description(options.translator.t("cli.models.use.description"))
    .option("--agent", options.translator.t("cli.models.use.option.agent"))
    .option("--chat", options.translator.t("cli.models.use.option.chat"))
    .option("--json", options.translator.t("cli.models.option.json"));

  useCommand.action(
    options.usageLogging.track(
      { area: "system", command: "models.use", options: () => useCommand.opts() },
      async (id: string) => {
        const commandOptions = useCommand.opts<{
          agent?: boolean;
          chat?: boolean;
          json?: boolean;
        }>();

        if (commandOptions.agent === true && commandOptions.chat === true) {
          throw new Error("Use only one of --agent or --chat.");
        }

        const role =
          commandOptions.agent === true
            ? "agent"
            : commandOptions.chat === true
              ? "chat"
              : undefined;
        printResult(
          await modelsCapability().execute({ action: "use", id, role }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );
}
