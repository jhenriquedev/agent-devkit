import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";
import {
  SurfaceCapabilitiesSchema,
  type SurfaceCapability,
  type SurfaceKnowledge,
  SurfaceKnowledgeSchema,
  type SurfaceLoop,
  SurfaceLoopSchema,
  type SurfacePrompt,
  type SurfacePromptInput,
  SurfacePromptSchema,
  type SurfaceSkill,
  SurfaceSkillSchema,
} from "../bases/surface";

export class SurfaceLoader {
  readonly #surfaceDirectory: string;

  constructor(surfaceDirectory: string) {
    this.#surfaceDirectory = surfaceDirectory;
  }

  async capabilities(): Promise<Result<AgentDevKitErrorCode, SurfaceCapability[]>> {
    const payload = await this.#readJson("capabilities.json");

    if (payload.isErr()) {
      return Result.fail(payload.unwrapError());
    }

    const parsed = SurfaceCapabilitiesSchema.safeParse(payload.unwrap());
    return parsed.success
      ? Result.ok(parsed.data.capabilities)
      : Result.fail(ErrorCodes.InvalidInput);
  }

  async knowledge(): Promise<Result<AgentDevKitErrorCode, SurfaceKnowledge>> {
    const payload = await this.#readJson("knowledge.json");

    if (payload.isErr()) {
      return Result.fail(payload.unwrapError());
    }

    const parsed = SurfaceKnowledgeSchema.safeParse(payload.unwrap());
    return parsed.success ? Result.ok(parsed.data) : Result.fail(ErrorCodes.InvalidInput);
  }

  async loop(): Promise<Result<AgentDevKitErrorCode, SurfaceLoop>> {
    const payload = await this.#readJson("loop.json");

    if (payload.isErr()) {
      return Result.fail(payload.unwrapError());
    }

    const parsed = SurfaceLoopSchema.safeParse(payload.unwrap());
    return parsed.success ? Result.ok(parsed.data) : Result.fail(ErrorCodes.InvalidInput);
  }

  async prompt(
    input: SurfacePromptInput = {},
  ): Promise<Result<AgentDevKitErrorCode, SurfacePrompt>> {
    const payload = await this.#readJson("prompt.json");

    if (payload.isErr()) {
      return Result.fail(payload.unwrapError());
    }

    const parsed = SurfacePromptSchema.safeParse(payload.unwrap());

    if (!parsed.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    return Result.ok({
      ...parsed.data,
      templates: parsed.data.templates
        .filter(
          (template) => input.capabilityId === undefined || template.id === input.capabilityId,
        )
        .map((template) => ({
          ...template,
          template: this.#renderTemplate(template.template, input.variables ?? {}),
        })),
    });
  }

  async skill(): Promise<Result<AgentDevKitErrorCode, SurfaceSkill>> {
    const payload = await this.#readJson("skill.json");

    if (payload.isErr()) {
      return Result.fail(payload.unwrapError());
    }

    const parsed = SurfaceSkillSchema.safeParse(payload.unwrap());
    return parsed.success ? Result.ok(parsed.data) : Result.fail(ErrorCodes.InvalidInput);
  }

  async #readJson(fileName: string): Promise<Result<AgentDevKitErrorCode, unknown>> {
    try {
      return Result.ok(JSON.parse(await readFile(join(this.#surfaceDirectory, fileName), "utf8")));
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  #renderTemplate(template: string, variables: Record<string, string>): string {
    return Object.entries(variables).reduce(
      (current, [key, value]) => current.replaceAll(`{{${key}}}`, value),
      template,
    );
  }
}
