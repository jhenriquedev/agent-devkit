import type { ToolRuntimeResult, ToolRuntimeTool } from "../../infra/bases/tool_runtime";

export type McpToolInput = Record<string, unknown> & {
  _agent?: {
    approved?: boolean;
  };
};

export function inputSchemaWithAgentControl(tool: ToolRuntimeTool): Record<string, unknown> {
  const schema = structuredClone(tool.inputSchema);
  const properties =
    typeof schema.properties === "object" && schema.properties !== null
      ? (schema.properties as Record<string, unknown>)
      : {};

  return {
    ...schema,
    type: "object",
    properties: {
      ...properties,
      _agent: {
        additionalProperties: false,
        description: "Agent DevKit MCP control metadata. Removed before capability execution.",
        properties: {
          approved: {
            description: "Explicitly approve a capability that requires approval.",
            type: "boolean",
          },
        },
        type: "object",
      },
    },
  };
}

export function splitMcpToolInput(input: unknown): {
  approved?: boolean;
  capabilityInput: unknown;
} {
  if (input === null || typeof input !== "object" || Array.isArray(input)) {
    return { capabilityInput: input };
  }

  const { _agent, ...capabilityInput } = input as McpToolInput;
  const approved =
    _agent !== undefined && typeof _agent === "object" && _agent.approved === true
      ? true
      : undefined;

  return {
    approved,
    capabilityInput,
  };
}

export function runtimeResultToMcpContent(result: ToolRuntimeResult) {
  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(result, null, 2),
      },
    ],
    isError: result.status !== "succeeded",
  };
}
