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

  const normalized = {
    ...schema,
    type: "object",
    properties: { ...properties },
  };

  if (!tool.approval.required) {
    return normalized;
  }

  return {
    ...normalized,
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

function isStructuredObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function hasObjectOutputSchema(tool: ToolRuntimeTool): boolean {
  return isStructuredObject(tool.outputSchema) && tool.outputSchema.type === "object";
}

export function runtimeResultToMcpContent(
  result: ToolRuntimeResult,
  includeStructuredContent = false,
) {
  const isError = result.status !== "succeeded";
  const content = [
    {
      type: "text" as const,
      text: JSON.stringify(result, null, 2),
    },
  ];

  if (!isError && includeStructuredContent && isStructuredObject(result.output)) {
    return { content, isError, structuredContent: result.output };
  }

  return { content, isError };
}
