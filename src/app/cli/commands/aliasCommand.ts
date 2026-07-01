import { homedir } from "node:os";
import type { Command } from "commander";
import type { AgentDevKitErrorCode } from "../../../infra/bases/errors";
import type { Translator } from "../../../infra/bases/i18n";
import type { Result } from "../../../infra/bases/result";
import {
  type CliAliasResult,
  createUserModuleBindings,
  formatCliAliasText,
} from "../../../modules/user/user.index";
import { wantsJson } from "../command_options";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterAliasCommandOptions = {
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

function cliAliasCapability() {
  const bindings = createUserModuleBindings({ homeDirectory: homedir() });

  if (bindings.isErr()) {
    throw new Error(bindings.unwrapError());
  }

  return bindings.unwrap().capabilities.cliAlias;
}

function printResult(
  result: Result<AgentDevKitErrorCode, CliAliasResult>,
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

  console.log(formatCliAliasText(payload, translator));
}

export function registerAliasCommand(program: Command, options: RegisterAliasCommandOptions): void {
  const aliasCommand = program
    .command("alias")
    .description(options.translator.t("cli.alias.description"))
    .option("--json", options.translator.t("cli.alias.option.json"))
    .action(
      options.usageLogging.track(
        { area: "user", command: "alias", options: () => aliasCommand.opts() },
        async (commandOptions: { json?: boolean }) => {
          printResult(
            await cliAliasCapability().execute({ action: "status" }),
            options.translator,
            wantsJson(commandOptions),
          );
        },
      ),
    );

  const setCommand = aliasCommand
    .command("set")
    .argument("<name>", options.translator.t("cli.alias.argument.name"))
    .description(options.translator.t("cli.alias.set.description"))
    .option("--force", options.translator.t("cli.alias.option.force"))
    .option("--json", options.translator.t("cli.alias.option.json"));

  setCommand.action(
    options.usageLogging.track(
      { area: "user", command: "alias.set", options: () => setCommand.opts() },
      async (name: string, commandOptions: { force?: boolean; json?: boolean }) => {
        printResult(
          await cliAliasCapability().execute({
            action: "set",
            force: commandOptions.force,
            name,
          }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const removeCommand = aliasCommand
    .command("remove")
    .description(options.translator.t("cli.alias.remove.description"))
    .option("--json", options.translator.t("cli.alias.option.json"));

  removeCommand.action(
    options.usageLogging.track(
      { area: "user", command: "alias.remove", options: () => removeCommand.opts() },
      async (commandOptions: { json?: boolean }) => {
        printResult(
          await cliAliasCapability().execute({ action: "remove" }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const syncCommand = aliasCommand
    .command("sync")
    .description(options.translator.t("cli.alias.sync.description"))
    .option("--json", options.translator.t("cli.alias.option.json"));

  syncCommand.action(
    options.usageLogging.track(
      { area: "user", command: "alias.sync", options: () => syncCommand.opts() },
      async (commandOptions: { json?: boolean }) => {
        printResult(
          await cliAliasCapability().execute({ action: "sync" }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const shellCommand = aliasCommand
    .command("shell")
    .description(options.translator.t("cli.alias.shell.description"))
    .option("--json", options.translator.t("cli.alias.option.json"));

  shellCommand.action(
    options.usageLogging.track(
      { area: "user", command: "alias.shell", options: () => shellCommand.opts() },
      async (commandOptions: { json?: boolean }) => {
        const result = await cliAliasCapability().execute({ action: "shell" });

        if (wantsJson(commandOptions)) {
          printResult(result, options.translator, true);
          return;
        }

        if (result.isErr()) {
          throw new Error(result.unwrapError());
        }

        console.log(result.unwrap().shellCommand);
      },
    ),
  );
}
