import { homedir } from "node:os";
import { createInterface } from "node:readline/promises";
import type { Translator } from "../../infra/bases/i18n";
import { ModelCatalogLoader } from "../../infra/models/model_catalog";
import { createModelsModuleBindings } from "../../modules/models/models.index";

function affirmative(answer: string): boolean {
  const normalized = answer.trim().toLowerCase();
  return normalized === "y" || normalized === "yes" || normalized === "s" || normalized === "sim";
}

/**
 * On the first interactive `agent` run, confirm a local model is available.
 * If none is installed, offer to download the recommended one. Never blocks the
 * tool: any failure or a non-interactive terminal falls through silently.
 */
export async function ensureFirstRunModel(translator: Translator): Promise<void> {
  const bindings = createModelsModuleBindings({ homeDirectory: homedir() });

  if (bindings.isErr()) {
    return;
  }

  const registry = bindings.unwrap().capabilities.registry;
  const models = await registry.execute({ action: "list" });

  if (models.isErr()) {
    return;
  }

  const modelsResult = models.unwrap();

  if (modelsResult.action !== "list" || modelsResult.models.some((model) => model.installed)) {
    return;
  }

  const recommended = await new ModelCatalogLoader().recommended();
  const entry = recommended.isOk() ? recommended.unwrap() : undefined;

  if (entry === undefined) {
    return;
  }

  const interactive = process.stdin.isTTY === true && process.stdout.isTTY === true;

  if (!interactive) {
    process.stderr.write(`${translator.t("cli.firstRun.hint", { id: entry.id })}\n`);
    return;
  }

  const readline = createInterface({ input: process.stdin, output: process.stdout });

  try {
    const answer = await readline.question(
      `${translator.t("cli.firstRun.prompt", { id: entry.id })} `,
    );

    if (!affirmative(answer)) {
      return;
    }

    process.stdout.write(`${translator.t("cli.models.install.progress", { id: entry.id })}\n`);

    const result = await registry.execute({ action: "install", id: entry.id });

    if (result.isErr()) {
      process.stderr.write(`${translator.t("cli.firstRun.failed", { id: entry.id })}\n`);
      return;
    }

    await registry.execute({ action: "use", id: entry.id });
    process.stdout.write(`${translator.t("cli.firstRun.installed", { id: entry.id })}\n`);
  } finally {
    readline.close();
  }
}
