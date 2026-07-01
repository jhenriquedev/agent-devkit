import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import type { ToolRuntime } from "../../infra/bases/tool_runtime";
import { createAgentMcpServer } from "./mcp_server";

export type StartMcpHttpServerOptions = {
  allowedOrigins?: string[];
  host: string;
  packageName: string;
  port: number;
  runtime: ToolRuntime;
  version: string;
};

const endpointPath = "/mcp";

function isOriginAllowed(origin: string | undefined, allowedOrigins: string[]): boolean {
  if (origin === undefined) {
    return true;
  }

  return allowedOrigins.includes(origin);
}

function writeText(res: ServerResponse, statusCode: number, text: string): void {
  res.writeHead(statusCode, { "content-type": "text/plain; charset=utf-8" });
  res.end(text);
}

export async function startMcpHttpServer(options: StartMcpHttpServerOptions): Promise<Server> {
  const httpServer = createServer(async (req: IncomingMessage, res: ServerResponse) => {
    if (req.url === undefined || new URL(req.url, "http://127.0.0.1").pathname !== endpointPath) {
      writeText(res, 404, "Not found");
      return;
    }

    if (req.method !== "POST" && req.method !== "GET") {
      writeText(res, 405, "Method not allowed");
      return;
    }

    if (!isOriginAllowed(req.headers.origin, options.allowedOrigins ?? [])) {
      writeText(res, 403, "Forbidden origin");
      return;
    }

    try {
      const server = createAgentMcpServer(options);
      const transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: undefined,
      });

      await server.connect(transport);
      res.on("close", () => {
        void transport.close();
        void server.close();
      });
      await transport.handleRequest(req, res);
    } catch (error) {
      if (!res.headersSent) {
        writeText(res, 500, error instanceof Error ? error.message : "MCP request failed");
      } else {
        res.end();
      }
    }
  });

  await new Promise<void>((resolve) => {
    httpServer.listen(options.port, options.host, resolve);
  });

  return httpServer;
}
