import { homedir } from "node:os";
import type { Command } from "commander";
import type { AgentDevKitErrorCode } from "../../../infra/bases/errors";
import type { Result } from "../../../infra/bases/result";
import type { PreferencesResult } from "../../../modules/user/user.index";
import { createUserModuleBindings, formatPreferencesText } from "../../../modules/user/user.index";

function preferencesCapability() {
  const bindings = createUserModuleBindings({ homeDirectory: homedir() });

  if (bindings.isErr()) {
    throw new Error(bindings.unwrapError());
  }

  return bindings.unwrap().capabilities.preferences;
}

function wantsJson(options?: { json?: boolean }): boolean {
  return options?.json === true || process.argv.includes("--json");
}

function printResult(result: Result<AgentDevKitErrorCode, PreferencesResult>, json?: boolean) {
  if (result.isErr()) {
    throw new Error(result.unwrapError());
  }

  const payload = result.unwrap();

  if (json === true) {
    console.log(JSON.stringify(payload, null, 2));
    return;
  }

  console.log(formatPreferencesText(payload));
}

export function registerPreferencesCommand(program: Command): void {
  const preferences = program
    .command("preferences")
    .alias("prefs")
    .description("view and update Agent DevKit user preferences")
    .option("--json", "print preferences as JSON")
    .action(async (options: { json?: boolean }) => {
      await printResult(
        await preferencesCapability().execute({ action: "view" }),
        wantsJson(options),
      );
    });

  preferences
    .command("themes")
    .description("list available themes")
    .option("--json", "print themes as JSON")
    .action(async (options: { json?: boolean }) => {
      await printResult(
        await preferencesCapability().execute({ action: "view" }),
        wantsJson(options),
      );
    });

  const setThemeCommand = preferences
    .command("set-theme")
    .argument("<theme>", "theme id to select")
    .description("set the active user theme")
    .option("--json", "print update result as JSON");

  setThemeCommand.action(async (theme: string) => {
    const options = setThemeCommand.opts<{ json?: boolean }>();
    await printResult(
      await preferencesCapability().execute({ action: "set-theme", theme }),
      wantsJson(options),
    );
  });

  const updateCommand = preferences
    .command("update")
    .description("update user preferences")
    .option("--theme <theme>", "theme id to select")
    .option("--json", "print update result as JSON");

  updateCommand.action(async () => {
    const options = updateCommand.opts<{ json?: boolean; theme?: string }>();
    if (options.theme === undefined) {
      await printResult(
        await preferencesCapability().execute({ action: "view" }),
        wantsJson(options),
      );
      return;
    }

    await printResult(
      await preferencesCapability().execute({ action: "set-theme", theme: options.theme }),
      wantsJson(options),
    );
  });
}
