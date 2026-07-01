import { homedir } from "node:os";
import type { Command } from "commander";
import type { AgentDevKitErrorCode } from "../../../infra/bases/errors";
import type { LanguageId, Translator } from "../../../infra/bases/i18n";
import type { Result } from "../../../infra/bases/result";
import type { PreferencesResult } from "../../../modules/user/user.index";
import { createUserModuleBindings, formatPreferencesText } from "../../../modules/user/user.index";
import { parsePositiveInteger, wantsJson } from "../command_options";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

function preferencesCapability() {
  const bindings = createUserModuleBindings({ homeDirectory: homedir() });

  if (bindings.isErr()) {
    throw new Error(bindings.unwrapError());
  }

  return bindings.unwrap().capabilities.preferences;
}

type RegisterPreferencesCommandOptions = {
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

function printResult(
  result: Result<AgentDevKitErrorCode, PreferencesResult>,
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

  console.log(formatPreferencesText(payload, translator));
}

export function registerPreferencesCommand(
  program: Command,
  options: RegisterPreferencesCommandOptions,
): void {
  const registerOptions = options;
  const preferences = program
    .command("preferences")
    .alias("prefs")
    .description(registerOptions.translator.t("cli.preferences.description"))
    .option("--json", registerOptions.translator.t("cli.preferences.option.json"))
    .action(
      registerOptions.usageLogging.track(
        {
          area: "user",
          command: "preferences",
          options: () => preferences.opts(),
        },
        async (commandOptions: { json?: boolean }) => {
          await printResult(
            await preferencesCapability().execute({ action: "view" }),
            registerOptions.translator,
            wantsJson(commandOptions),
          );
        },
      ),
    );

  const themesCommand = preferences
    .command("themes")
    .description(registerOptions.translator.t("cli.preferences.themes.description"))
    .option("--json", registerOptions.translator.t("cli.preferences.themes.option.json"));

  themesCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "preferences.themes",
        options: () => themesCommand.opts(),
      },
      async (commandOptions: { json?: boolean }) => {
        await printResult(
          await preferencesCapability().execute({ action: "view" }),
          registerOptions.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const languagesCommand = preferences
    .command("languages")
    .description(registerOptions.translator.t("cli.preferences.languages.description"))
    .option("--json", registerOptions.translator.t("cli.preferences.languages.option.json"));

  languagesCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "preferences.languages",
        options: () => languagesCommand.opts(),
      },
      async (commandOptions: { json?: boolean }) => {
        await printResult(
          await preferencesCapability().execute({ action: "view" }),
          registerOptions.translator,
          wantsJson(commandOptions),
        );
      },
    ),
  );

  const setThemeCommand = preferences
    .command("set-theme")
    .argument("<theme>", registerOptions.translator.t("cli.preferences.setTheme.argument"))
    .description(registerOptions.translator.t("cli.preferences.setTheme.description"))
    .option("--json", registerOptions.translator.t("cli.preferences.setTheme.option.json"));

  setThemeCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "preferences.set-theme",
        options: () => setThemeCommand.opts(),
      },
      async (theme: string) => {
        const options = setThemeCommand.opts<{ json?: boolean }>();
        await printResult(
          await preferencesCapability().execute({ action: "set-theme", theme }),
          registerOptions.translator,
          wantsJson(options),
        );
      },
    ),
  );

  const setLanguageCommand = preferences
    .command("set-language")
    .argument("<language>", registerOptions.translator.t("cli.preferences.setLanguage.argument"))
    .description(registerOptions.translator.t("cli.preferences.setLanguage.description"))
    .option("--json", registerOptions.translator.t("cli.preferences.setLanguage.option.json"));

  setLanguageCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "preferences.set-language",
        options: () => setLanguageCommand.opts(),
      },
      async (language: string) => {
        const options = setLanguageCommand.opts<{ json?: boolean }>();
        await printResult(
          await preferencesCapability().execute({
            action: "set-language",
            language: language as LanguageId,
          }),
          registerOptions.translator,
          wantsJson(options),
        );
      },
    ),
  );

  const setLogRetentionCommand = preferences
    .command("set-log-retention")
    .argument("<days>", registerOptions.translator.t("cli.preferences.setLogRetention.argument"))
    .description(registerOptions.translator.t("cli.preferences.setLogRetention.description"))
    .option("--json", registerOptions.translator.t("cli.preferences.setLogRetention.option.json"));

  setLogRetentionCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "preferences.set-log-retention",
        options: () => setLogRetentionCommand.opts(),
      },
      async (days: string) => {
        const options = setLogRetentionCommand.opts<{ json?: boolean }>();
        await printResult(
          await preferencesCapability().execute({
            action: "set-log-retention",
            logRetentionDays: parsePositiveInteger(days),
          }),
          registerOptions.translator,
          wantsJson(options),
        );
      },
    ),
  );

  const updateCommand = preferences
    .command("update")
    .description(registerOptions.translator.t("cli.preferences.update.description"))
    .option("--theme <theme>", registerOptions.translator.t("cli.preferences.update.option.theme"))
    .option(
      "--language <language>",
      registerOptions.translator.t("cli.preferences.update.option.language"),
    )
    .option(
      "--log-retention-days <days>",
      registerOptions.translator.t("cli.preferences.update.option.logRetentionDays"),
    )
    .option("--json", registerOptions.translator.t("cli.preferences.update.option.json"));

  updateCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "preferences.update",
        options: () => updateCommand.opts(),
      },
      async () => {
        const options = updateCommand.opts<{
          json?: boolean;
          language?: string;
          logRetentionDays?: string;
          theme?: string;
        }>();

        await printResult(
          await preferencesCapability().execute({
            action: "update",
            language: options.language as LanguageId | undefined,
            logRetentionDays:
              options.logRetentionDays === undefined
                ? undefined
                : parsePositiveInteger(options.logRetentionDays),
            theme: options.theme,
          }),
          registerOptions.translator,
          wantsJson(options),
        );
      },
    ),
  );

  const resetDefaultsCommand = preferences
    .command("reset-defaults")
    .description(registerOptions.translator.t("cli.preferences.resetDefaults.description"))
    .option("--json", registerOptions.translator.t("cli.preferences.resetDefaults.option.json"));

  resetDefaultsCommand.action(
    registerOptions.usageLogging.track(
      {
        area: "user",
        command: "preferences.reset-defaults",
        options: () => resetDefaultsCommand.opts(),
      },
      async () => {
        const options = resetDefaultsCommand.opts<{ json?: boolean }>();
        await printResult(
          await preferencesCapability().execute({ action: "reset-defaults" }),
          registerOptions.translator,
          wantsJson(options),
        );
      },
    ),
  );
}
