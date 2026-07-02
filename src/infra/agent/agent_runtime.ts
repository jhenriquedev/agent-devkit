import { z } from "zod";
import type { BrainProviderPort, BrainRequest } from "../bases/brain";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { type AgentPrompt, AgentPromptSchema, type PromptMessage } from "../bases/prompt";
import { Result } from "../bases/result";
import type { ToolRuntime, ToolRuntimeResult, ToolRuntimeTool } from "../bases/tool_runtime";

export const AgentDecisionSchema = z.discriminatedUnion("action", [
  z.object({ action: z.literal("tool"), input: z.unknown(), tool: z.string().min(1) }),
  z.object({ action: z.literal("final"), reply: z.string() }),
]);

export type AgentDecision = z.infer<typeof AgentDecisionSchema>;

const agentDecisionJsonSchema: Record<string, unknown> = {
  type: "object",
  properties: {
    action: { type: "string", enum: ["tool", "final"] },
    input: { type: "object" },
    reply: { type: "string" },
    tool: { type: "string" },
  },
  required: ["action"],
};

export type AgentStep = {
  ok: boolean;
  summary: string;
  tool: string;
};

export type AgentRunResult = {
  reply: string;
  steps: AgentStep[];
};

export type AgentStreamEvent =
  | { type: "tool"; tool: string }
  | { type: "observation"; ok: boolean; summary: string; tool: string }
  | { type: "final"; reply: string };

export type AgentRunInput = {
  approved?: boolean;
  approvedTools?: string[];
  history?: { content: string; role: "assistant" | "user" }[];
  maxSteps?: number;
  onEvent?: (event: AgentStreamEvent) => void;
  task: string;
};

export type AgentRuntimeOptions = {
  brainProvider: BrainProviderPort;
  toolRuntime: ToolRuntime;
};

function summarize(value: unknown): string {
  const text = typeof value === "string" ? value : JSON.stringify(value ?? "");
  const compact = text.replaceAll(/\s+/g, " ").trim();
  return compact.length > 240 ? `${compact.slice(0, 240)}…` : compact;
}

function observationSummary(result: ToolRuntimeResult): string {
  if (result.status === "succeeded") {
    return summarize(result.output);
  }

  return `${result.status}${result.error === undefined ? "" : `: ${result.error.message}`}`;
}

/**
 * Single-agent tool-use loop over the ToolRuntime. Lives outside the capability
 * registry on purpose (so the agent is not a tool that can call itself). Uses a
 * JSON-constrained decision each turn: run a tool, or answer.
 */
export class AgentRuntime {
  readonly #brain: BrainProviderPort;
  readonly #tools: ToolRuntime;

  constructor(options: AgentRuntimeOptions) {
    this.#brain = options.brainProvider;
    this.#tools = options.toolRuntime;
  }

  async run(input: AgentRunInput): Promise<Result<AgentDevKitErrorCode, AgentRunResult>> {
    const generateStructured = this.#brain.generateStructured?.bind(this.#brain);

    if (generateStructured === undefined) {
      return Result.fail(ErrorCodes.BrainProviderUnavailable);
    }

    const maxSteps = input.maxSteps ?? 6;
    const steps: AgentStep[] = [];
    const transcript: PromptMessage[] = (input.history ?? []).map((message) => ({
      content: message.content,
      role: message.role,
    }));
    const tools = this.#tools.listTools();

    for (let step = 0; step < maxSteps; step += 1) {
      const prompt = this.#buildPrompt(input.task, transcript, tools);
      const request: BrainRequest = {
        options: { provider: "local", role: "agent" },
        prompt,
        schema: "agent-devkit.brain-request/v1",
      };
      const structured = await generateStructured(request, agentDecisionJsonSchema);

      if (structured.isErr()) {
        return Result.fail(structured.unwrapError());
      }

      const decision = AgentDecisionSchema.safeParse(structured.unwrap().json);

      if (!decision.success) {
        return Result.ok({ reply: structured.unwrap().raw.trim(), steps });
      }

      if (decision.data.action === "final") {
        input.onEvent?.({ reply: decision.data.reply, type: "final" });
        return Result.ok({ reply: decision.data.reply, steps });
      }

      const tool = decision.data.tool;
      input.onEvent?.({ tool, type: "tool" });

      const execution = await this.#tools.execute({
        approved: this.#isApproved(tool, input),
        capabilityId: tool,
        input: decision.data.input,
        interface: "agent",
        requestedBy: "agent.run",
      });
      const ok = execution.status === "succeeded";
      const summary = observationSummary(execution);

      steps.push({ ok, summary, tool });
      input.onEvent?.({ ok, summary, tool, type: "observation" });
      transcript.push({ content: `Observation from ${tool}: ${summary}`, role: "tool" });

      if (execution.status === "approval_required") {
        return Result.ok({
          reply: `A ferramenta ${tool} requer aprovação explícita. Reexecute autorizando para continuar.`,
          steps,
        });
      }
    }

    return Result.ok({
      reply: "Limite de passos do agente atingido sem uma resposta final.",
      steps,
    });
  }

  #isApproved(tool: string, input: AgentRunInput): boolean {
    if (input.approvedTools !== undefined) {
      return input.approvedTools.includes(tool);
    }

    return input.approved === true;
  }

  #buildPrompt(task: string, transcript: PromptMessage[], tools: ToolRuntimeTool[]): AgentPrompt {
    const toolList = tools
      .map((tool) => `- ${tool.id} (${tool.risk}): ${tool.description}`)
      .join("\n");
    const instruction = [
      `Tarefa do usuário: ${task}`,
      "",
      "Ferramentas disponíveis:",
      toolList,
      "",
      'Responda SOMENTE com JSON. Para usar uma ferramenta: {"action":"tool","tool":"<id>","input":{...}}. Para responder ao usuário: {"action":"final","reply":"<texto>"}. Uma ação por vez.',
    ].join("\n");

    return AgentPromptSchema.parse({
      agent: {
        behavior: "balanced",
        characterId: "agent",
        detailLevel: "concise",
        name: "Agent",
        tone: "direct",
        traits: [],
      },
      context: { knowledge: [] },
      locale: "pt-BR",
      messages: transcript,
      output: { format: "json", language: "pt-BR" },
      policies: {
        allowToolCalls: true,
        approvalRequired: false,
        maxToolCalls: maxToolCallsFor(tools),
      },
      schema: "agent-devkit.prompt/v1",
      task: { userMessage: instruction },
      tools: tools.map((tool) => ({
        description: tool.description,
        id: tool.id,
        inputSchema: tool.inputSchema,
        risk: tool.risk,
      })),
    });
  }
}

function maxToolCallsFor(tools: ToolRuntimeTool[]): number {
  return Math.max(1, tools.length);
}
