import type {
  BrainProviderPort,
  BrainRequest,
  BrainResponse,
  BrainStreamHandler,
  BrainStructuredResponse,
} from "../bases/brain";
import type { AgentDevKitErrorCode } from "../bases/errors";
import { Result } from "../bases/result";

function reply(request: BrainRequest): BrainResponse {
  const text = `${request.prompt.agent.name}: Entendi. Vou responder no contexto da sessão atual: "${request.prompt.task.userMessage}".`;
  const inputTokens = request.prompt.messages
    .map((message) => message.content.split(/\s+/g).filter(Boolean).length)
    .reduce((total, count) => total + count, 0);
  const outputTokens = text.split(/\s+/g).filter(Boolean).length;

  return {
    finishReason: "stop",
    model: request.options.model ?? "mock-chat",
    provider: "mock",
    schema: "agent-devkit.brain-response/v1",
    text,
    usage: {
      inputTokens,
      outputTokens,
      totalTokens: inputTokens + outputTokens,
    },
  };
}

export class MockBrainProvider implements BrainProviderPort {
  async generate(request: BrainRequest): Promise<Result<AgentDevKitErrorCode, BrainResponse>> {
    return Result.ok(reply(request));
  }

  async generateStream(
    request: BrainRequest,
    onToken: BrainStreamHandler,
  ): Promise<Result<AgentDevKitErrorCode, BrainResponse>> {
    const response = reply(request);
    onToken(response.text);
    return Result.ok(response);
  }

  async generateStructured(
    request: BrainRequest,
    _jsonSchema: Record<string, unknown>,
  ): Promise<Result<AgentDevKitErrorCode, BrainStructuredResponse>> {
    const raw = JSON.stringify({ action: "final", reply: reply(request).text });
    return Result.ok({ json: JSON.parse(raw), raw });
  }
}
