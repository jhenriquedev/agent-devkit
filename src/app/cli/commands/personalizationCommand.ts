import { homedir } from "node:os";
import type { Command } from "commander";
import type { AgentDevKitErrorCode } from "../../../infra/bases/errors";
import type { Translator } from "../../../infra/bases/i18n";
import type { Result } from "../../../infra/bases/result";
import type { PersonalizationResult } from "../../../modules/user/user.index";
import {
  createUserModuleBindings,
  formatPersonalizationText,
} from "../../../modules/user/user.index";
import { wantsJson } from "../command_options";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

function personalizationCapability() {
  const bindings = createUserModuleBindings({ homeDirectory: homedir() });

  if (bindings.isErr()) {
    throw new Error(bindings.unwrapError());
  }

  return bindings.unwrap().capabilities.personalization;
}

type RegisterPersonalizationCommandOptions = {
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

type UpdateCommandOptions = {
  behavior?: string;
  character?: string;
  detail?: string;
  gender?: string;
  json?: boolean;
  name?: string;
  tone?: string;
  traits?: string;
};

function parseTraits(value: string | undefined): string[] | undefined {
  if (value === undefined) {
    return undefined;
  }

  return value
    .split(",")
    .map((trait) => trait.trim())
    .filter((trait) => trait.length > 0);
}

function printResult(
  result: Result<AgentDevKitErrorCode, PersonalizationResult>,
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

  console.log(formatPersonalizationText(payload, translator));
}

export function registerPersonalizationCommand(
  program: Command,
  options: RegisterPersonalizationCommandOptions,
): void {
  const registerOptions = options;
  const personalization = program
    .command("personalization")
    .alias("personalize")
    .description(registerOptions.translator.t("cli.personalization.description"))
    .option("--json", registerOptions.translator.t("cli.personalization.option.json"))
    .action(
      registerOptions.usageLogging.track(
        {
          area: "user",
          command: "personalization",
          options: () => personalization.opts(),
        },
        async (commandOptions: { json?: boolean }) => {
          await printResult(
            await personalizationCapability().execute({ action: "view" }),
            registerOptions.translator,
            wantsJson(commandOptions),
          );
        },
      ),
    );

  const presetsCommand = personalization
    .command("characters")
    .alias("presets")
    .description(registerOptions.translator.t("cli.personalization.characters.description"))
    .option("--json", registerOptions.translator.t("cli.personalization.characters.option.json"));

  presetsCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "personalization.presets",
        options: () => presetsCommand.opts(),
      },
      async (commandOptions: { json?: boolean }) => {
        await printResult(
          await personalizationCapability().execute({ action: "list-characters" }),
          registerOptions.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const selectCommand = personalization
    .command("select")
    .argument("<character>", registerOptions.translator.t("cli.personalization.select.argument"))
    .description(registerOptions.translator.t("cli.personalization.select.description"))
    .option("--json", registerOptions.translator.t("cli.personalization.select.option.json"));

  selectCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "personalization.select",
        options: () => selectCommand.opts(),
      },
      async (character: string) => {
        const commandOptions = selectCommand.opts<{ json?: boolean }>();

        await printResult(
          await personalizationCapability().execute({
            action: "select-preset",
            characterId: character,
          }),
          registerOptions.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const updateCommand = personalization
    .command("update")
    .description(registerOptions.translator.t("cli.personalization.update.description"))
    .option("--name <name>", registerOptions.translator.t("cli.personalization.update.option.name"))
    .option(
      "--character <character>",
      registerOptions.translator.t("cli.personalization.update.option.character"),
    )
    .option(
      "--behavior <behavior>",
      registerOptions.translator.t("cli.personalization.update.option.behavior"),
    )
    .option("--tone <tone>", registerOptions.translator.t("cli.personalization.update.option.tone"))
    .option(
      "--detail <detail>",
      registerOptions.translator.t("cli.personalization.update.option.detail"),
    )
    .option(
      "--gender <gender>",
      registerOptions.translator.t("cli.personalization.update.option.gender"),
    )
    .option(
      "--traits <traits>",
      registerOptions.translator.t("cli.personalization.update.option.traits"),
    )
    .option("--json", registerOptions.translator.t("cli.personalization.update.option.json"));

  updateCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "personalization.update",
        options: () => updateCommand.opts(),
      },
      async () => {
        const commandOptions = updateCommand.opts<UpdateCommandOptions>();

        await printResult(
          await personalizationCapability().execute({
            action: "update",
            profile: {
              name: commandOptions.name,
              behavior: commandOptions.behavior as never,
              characterId: commandOptions.character,
              detailLevel: commandOptions.detail as never,
              gender: commandOptions.gender as never,
              tone: commandOptions.tone as never,
              traits: parseTraits(commandOptions.traits),
            },
          }),
          registerOptions.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const createCommand = personalization
    .command("create")
    .requiredOption(
      "--id <id>",
      registerOptions.translator.t("cli.personalization.create.option.id"),
    )
    .requiredOption(
      "--name <name>",
      registerOptions.translator.t("cli.personalization.create.option.name"),
    )
    .option("--from <id>", registerOptions.translator.t("cli.personalization.create.option.from"))
    .option("--json", registerOptions.translator.t("cli.personalization.create.option.json"));

  createCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "personalization.create",
        options: () => createCommand.opts(),
      },
      async () => {
        const commandOptions = createCommand.opts<{
          from?: string;
          id: string;
          json?: boolean;
          name: string;
        }>();

        await printResult(
          await personalizationCapability().execute({
            action: "create-character",
            character: {
              fromCharacterId: commandOptions.from,
              id: commandOptions.id,
              name: commandOptions.name,
            },
          }),
          registerOptions.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const importSpriteCommand = personalization
    .command("import-sprite")
    .requiredOption(
      "--character <character>",
      registerOptions.translator.t("cli.personalization.importSprite.option.character"),
    )
    .requiredOption(
      "--path <path>",
      registerOptions.translator.t("cli.personalization.importSprite.option.path"),
    )
    .option("--json", registerOptions.translator.t("cli.personalization.importSprite.option.json"));

  importSpriteCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "personalization.import-sprite",
        options: () => importSpriteCommand.opts(),
      },
      async () => {
        const commandOptions = importSpriteCommand.opts<{
          character: string;
          json?: boolean;
          path: string;
        }>();

        await printResult(
          await personalizationCapability().execute({
            action: "import-sprite",
            characterId: commandOptions.character,
            sourcePath: commandOptions.path,
          }),
          registerOptions.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const resetCurrentCommand = personalization
    .command("reset-current")
    .description(registerOptions.translator.t("cli.personalization.resetCurrent.description"))
    .option("--json", registerOptions.translator.t("cli.personalization.resetCurrent.option.json"));

  resetCurrentCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "personalization.reset-current",
        options: () => resetCurrentCommand.opts(),
      },
      async () => {
        const commandOptions = resetCurrentCommand.opts<{ json?: boolean }>();

        await printResult(
          await personalizationCapability().execute({ action: "reset-current" }),
          registerOptions.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const resetDefaultsCommand = personalization
    .command("reset-defaults")
    .description(registerOptions.translator.t("cli.personalization.resetDefaults.description"))
    .option(
      "--json",
      registerOptions.translator.t("cli.personalization.resetDefaults.option.json"),
    );

  resetDefaultsCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "personalization.reset-defaults",
        options: () => resetDefaultsCommand.opts(),
      },
      async () => {
        const commandOptions = resetDefaultsCommand.opts<{ json?: boolean }>();

        await printResult(
          await personalizationCapability().execute({ action: "reset-defaults" }),
          registerOptions.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );
}
