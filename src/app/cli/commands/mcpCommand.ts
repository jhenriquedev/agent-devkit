import type { Command } from "commander";
import type { Translator } from "../../../infra/bases/i18n";
import { startMcpHttpServer } from "../../mcp/mcp_http_transport";
import { startMcpStdioServer } from "../../mcp/mcp_stdio_transport";
import { parsePositiveInteger } from "../command_options";
import { createCliToolRuntime } from "../toolRuntime";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterMcpCommandOptions = {
  currentVersion: string;
  packageName: string;
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

function runtime(options: RegisterMcpCommandOptions) {
  return createCliToolRuntime({
    currentVersion: options.currentVersion,
    packageName: options.packageName,
  });
}

async function runStdio(options: RegisterMcpCommandOptions): Promise<void> {
  await startMcpStdioServer({
    packageName: options.packageName,
    runtime: runtime(options),
    version: options.currentVersion,
  });
}

export function registerMcpCommand(program: Command, options: RegisterMcpCommandOptions): void {
  const mcpCommand = program
    .command("mcp")
    .description(options.translator.t("cli.mcp.description"));

  mcpCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "mcp.stdio",
        createStateIfMissing: false,
        options: () => ({}),
      },
      async () => {
        await runStdio(options);
      },
    ),
  );

  const stdioCommand = mcpCommand
    .command("stdio")
    .description(options.translator.t("cli.mcp.stdio.description"));

  stdioCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "mcp.stdio",
        createStateIfMissing: false,
        options: () => stdioCommand.opts(),
      },
      async () => {
        await runStdio(options);
      },
    ),
  );

  const httpCommand = mcpCommand
    .command("http")
    .description(options.translator.t("cli.mcp.http.description"))
    .option("--host <host>", options.translator.t("cli.mcp.http.option.host"), "127.0.0.1")
    .option("--port <port>", options.translator.t("cli.mcp.http.option.port"), "3333")
    .option(
      "--origin <origin...>",
      options.translator.t("cli.mcp.http.option.origin"),
      [] as string[],
    );

  httpCommand.action(
    options.usageLogging.track(
      {
        area: "system",
        command: "mcp.http",
        createStateIfMissing: false,
        options: () => httpCommand.opts(),
      },
      async (commandOptions: { host: string; origin: string[]; port: string }) => {
        if (commandOptions.host !== "127.0.0.1" && commandOptions.host !== "localhost") {
          throw new Error("MCP HTTP currently supports only localhost hosts.");
        }

        const server = await startMcpHttpServer({
          allowedOrigins: commandOptions.origin,
          host: commandOptions.host,
          packageName: options.packageName,
          port: parsePositiveInteger(commandOptions.port),
          runtime: runtime(options),
          version: options.currentVersion,
        });

        const address = server.address();
        const port =
          typeof address === "object" && address !== null ? address.port : commandOptions.port;
        process.stderr.write(
          `Agent DevKit MCP HTTP listening on http://${commandOptions.host}:${port}/mcp\n`,
        );
      },
    ),
  );
}
