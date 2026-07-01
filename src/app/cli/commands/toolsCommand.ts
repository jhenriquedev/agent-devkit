import type { Command } from "commander";
import type { Translator } from "../../../infra/bases/i18n";
import type { ToolRuntimeTool } from "../../../infra/bases/tool_runtime";
import { createCliToolRuntime } from "../toolRuntime";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterToolsCommandOptions = {
  currentVersion: string;
  packageName: string;
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

function formatToolsText(tools: ToolRuntimeTool[]): string {
  const rows = tools.map((tool) => ({
    id: tool.id,
    kind: tool.kind,
    module: tool.moduleId,
    risk: tool.risk,
  }));
  const widths = {
    id: Math.max("id".length, ...rows.map((row) => row.id.length)),
    kind: Math.max("kind".length, ...rows.map((row) => row.kind.length)),
    module: Math.max("module".length, ...rows.map((row) => row.module.length)),
    risk: Math.max("risk".length, ...rows.map((row) => row.risk.length)),
  };
  const line = (row: { id: string; kind: string; module: string; risk: string }) =>
    `${row.id.padEnd(widths.id)}  ${row.module.padEnd(widths.module)}  ${row.risk.padEnd(
      widths.risk,
    )}  ${row.kind.padEnd(widths.kind)}`;

  return [
    line({ id: "id", kind: "kind", module: "module", risk: "risk" }),
    line({
      id: "-".repeat(widths.id),
      kind: "-".repeat(widths.kind),
      module: "-".repeat(widths.module),
      risk: "-".repeat(widths.risk),
    }),
    ...rows.map(line),
  ].join("\n");
}

export function registerToolsCommand(program: Command, options: RegisterToolsCommandOptions): void {
  const toolsCommand = program
    .command("tools")
    .description(options.translator.t("cli.tools.description"))
    .option("--json", options.translator.t("cli.tools.option.json"));

  toolsCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "tools",
        createStateIfMissing: false,
        options: () => toolsCommand.opts(),
      },
      async (commandOptions: { json?: boolean }) => {
        const runtime = createCliToolRuntime({
          currentVersion: options.currentVersion,
          packageName: options.packageName,
        });
        const tools = runtime.listTools();

        if (commandOptions.json === true) {
          console.log(JSON.stringify({ tools }, null, 2));
          return;
        }

        console.log(formatToolsText(tools));
      },
    ),
  );
}
