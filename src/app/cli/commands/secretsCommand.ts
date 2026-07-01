import { homedir } from "node:os";
import { text } from "node:stream/consumers";
import type { Command } from "commander";
import type { AgentDevKitErrorCode } from "../../../infra/bases/errors";
import type { Translator } from "../../../infra/bases/i18n";
import type { Result } from "../../../infra/bases/result";
import type { SecretsVaultResult } from "../../../modules/secrets/secrets.index";
import {
  createSecretsModuleBindings,
  formatSecretsVaultText,
} from "../../../modules/secrets/secrets.index";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterSecretsCommandOptions = {
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

function secretsCapability() {
  const bindings = createSecretsModuleBindings({ homeDirectory: homedir() });

  if (bindings.isErr()) {
    throw new Error(bindings.unwrapError());
  }

  return bindings.unwrap().capabilities.vault;
}

function wantsJson(options?: { json?: boolean }): boolean {
  return options?.json === true || process.argv.includes("--json");
}

async function resolveSecretValue(options: { stdin?: boolean; value?: string }): Promise<string> {
  if (options.stdin === true && options.value !== undefined) {
    throw new Error("Use --stdin or --value, not both.");
  }

  if (options.stdin === true) {
    const value = (await text(process.stdin)).replace(/\r?\n$/, "");

    if (value.length === 0) {
      throw new Error("Secret value from stdin cannot be empty.");
    }

    return value;
  }

  if (options.value === undefined || options.value.length === 0) {
    throw new Error("Secret value is required. Use --stdin or --value.");
  }

  return options.value;
}

function printResult(
  result: Result<AgentDevKitErrorCode, SecretsVaultResult>,
  translator: Translator,
  json?: boolean,
) {
  if (result.isErr()) {
    throw new Error(result.unwrapError());
  }

  const payload = result.unwrap();

  if (json === true) {
    console.log(JSON.stringify(payload, null, 2));
    return;
  }

  console.log(formatSecretsVaultText(payload, translator));
}

export function registerSecretsCommand(
  program: Command,
  options: RegisterSecretsCommandOptions,
): void {
  const secretsCommand = program
    .command("secrets")
    .description(options.translator.t("cli.secrets.description"))
    .option("--json", options.translator.t("cli.secrets.option.json"));

  secretsCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "secrets",
        options: () => secretsCommand.opts(),
      },
      async (commandOptions: { json?: boolean }) => {
        await printResult(
          await secretsCapability().execute({ action: "list" }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const listCommand = secretsCommand
    .command("list")
    .description(options.translator.t("cli.secrets.list.description"))
    .option("--json", options.translator.t("cli.secrets.option.json"));

  listCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "secrets.list",
        options: () => listCommand.opts(),
      },
      async (commandOptions: { json?: boolean }) => {
        await printResult(
          await secretsCapability().execute({ action: "list" }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const setCommand = secretsCommand
    .command("set")
    .argument("<name>", options.translator.t("cli.secrets.argument.name"))
    .description(options.translator.t("cli.secrets.set.description"))
    .option("--json", options.translator.t("cli.secrets.option.json"))
    .option("--service <service>", options.translator.t("cli.secrets.set.option.service"))
    .option("--stdin", options.translator.t("cli.secrets.set.option.stdin"))
    .option("--value <value>", options.translator.t("cli.secrets.set.option.value"));

  setCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "secrets.set",
        options: () => setCommand.opts(),
        redactOptions: ["--value"],
      },
      async (name: string) => {
        const commandOptions = setCommand.opts<{
          json?: boolean;
          service?: string;
          stdin?: boolean;
          value?: string;
        }>();
        const value = await resolveSecretValue(commandOptions);
        await printResult(
          await secretsCapability().execute({
            action: "set",
            name,
            service: commandOptions.service,
            value,
          }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const showCommand = secretsCommand
    .command("show")
    .argument("<name>", options.translator.t("cli.secrets.argument.name"))
    .description(options.translator.t("cli.secrets.show.description"))
    .option("--json", options.translator.t("cli.secrets.option.json"))
    .option("--reveal", options.translator.t("cli.secrets.show.option.reveal"));

  showCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "secrets.show",
        options: () => showCommand.opts(),
      },
      async (name: string) => {
        const commandOptions = showCommand.opts<{ json?: boolean; reveal?: boolean }>();
        await printResult(
          await secretsCapability().execute({
            action: "show",
            name,
            reveal: commandOptions.reveal === true,
          }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const rotateCommand = secretsCommand
    .command("rotate")
    .argument("<name>", options.translator.t("cli.secrets.argument.name"))
    .description(options.translator.t("cli.secrets.rotate.description"))
    .option("--json", options.translator.t("cli.secrets.option.json"))
    .option("--service <service>", options.translator.t("cli.secrets.set.option.service"))
    .option("--stdin", options.translator.t("cli.secrets.set.option.stdin"))
    .option("--value <value>", options.translator.t("cli.secrets.set.option.value"));

  rotateCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "secrets.rotate",
        options: () => rotateCommand.opts(),
        redactOptions: ["--value"],
      },
      async (name: string) => {
        const commandOptions = rotateCommand.opts<{
          json?: boolean;
          service?: string;
          stdin?: boolean;
          value?: string;
        }>();
        const value = await resolveSecretValue(commandOptions);
        await printResult(
          await secretsCapability().execute({
            action: "rotate",
            name,
            service: commandOptions.service,
            value,
          }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const auditCommand = secretsCommand
    .command("audit")
    .argument("[name]", options.translator.t("cli.secrets.audit.argument.name"))
    .description(options.translator.t("cli.secrets.audit.description"))
    .option("--json", options.translator.t("cli.secrets.option.json"));

  auditCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "secrets.audit",
        options: () => auditCommand.opts(),
      },
      async (name: string | undefined) => {
        const commandOptions = auditCommand.opts<{ json?: boolean }>();
        await printResult(
          await secretsCapability().execute({ action: "audit", name }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const removeCommand = secretsCommand
    .command("remove")
    .alias("rm")
    .argument("<name>", options.translator.t("cli.secrets.argument.name"))
    .description(options.translator.t("cli.secrets.remove.description"))
    .option("--json", options.translator.t("cli.secrets.option.json"));

  removeCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "secrets.remove",
        options: () => removeCommand.opts(),
      },
      async (name: string) => {
        const commandOptions = removeCommand.opts<{ json?: boolean }>();
        await printResult(
          await secretsCapability().execute({ action: "remove", name }),
          options.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );
}
