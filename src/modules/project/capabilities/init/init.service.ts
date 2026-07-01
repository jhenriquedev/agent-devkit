import {
  BaseCapabilityService,
  type CapabilityExecution,
  defineCapabilityConfig,
} from "../../../../infra/bases/capability";
import type { AgentDevKitErrorCode } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import {
  type InitServiceOptions,
  InitServiceOptionsSchema,
  type ProjectInitFile,
  type ProjectInitResult,
  ProjectInitResultSchema,
} from "./init.entities";
import type { InitRepositoryPort } from "./init.repository";

type InitServiceDependencies = {
  appVersion: string;
  repository: InitRepositoryPort;
};

const projectFiles = [".agent-devkit/config.json", ".agent-devkit/agent-devkit.lock"];

export const initCapabilityConfig = defineCapabilityConfig({
  id: "project.init",
  moduleId: "project",
  name: "Init",
  description: "Initialize Agent DevKit project-local state files.",
  kind: "deterministic",
  risk: "writes-project-state",
} as const);

export class InitService
  extends BaseCapabilityService<typeof initCapabilityConfig, InitServiceDependencies>
  implements CapabilityExecution<InitServiceOptions, ProjectInitResult>
{
  readonly inputSchema = InitServiceOptionsSchema;
  readonly outputSchema = ProjectInitResultSchema;
  readonly #appVersion: string;
  readonly #repository: InitRepositoryPort;

  constructor(dependencies: InitServiceDependencies) {
    super(initCapabilityConfig, dependencies);
    this.#appVersion = dependencies.appVersion;
    this.#repository = dependencies.repository;
  }

  async execute(
    options: InitServiceOptions,
  ): Promise<Result<AgentDevKitErrorCode, ProjectInitResult>> {
    if (options.dryRun) {
      return Result.ok({
        status: "planned",
        version: this.#appVersion,
        project: {
          root: options.projectRoot,
        },
        planned: projectFiles,
        created: [],
        skipped: [],
      });
    }

    const skipped = await this.#repository.existingFiles(options.projectRoot, projectFiles);

    if (skipped.isErr()) {
      return Result.fail(skipped.unwrapError());
    }

    const skippedFiles = skipped.unwrap();
    const filesToCreate = this.#files().filter((file) => !skippedFiles.includes(file.path));

    if (filesToCreate.length > 0) {
      const write = await this.#repository.writeFiles(options.projectRoot, filesToCreate);

      if (write.isErr()) {
        return Result.fail(write.unwrapError());
      }
    }

    return Result.ok({
      status: filesToCreate.length > 0 ? "initialized" : "already-initialized",
      version: this.#appVersion,
      project: {
        root: options.projectRoot,
      },
      planned: projectFiles,
      created: filesToCreate.map((file) => file.path),
      skipped: skippedFiles,
    });
  }

  #files(): ProjectInitFile[] {
    return [
      {
        path: ".agent-devkit/config.json",
        content: {
          schema: "agent-devkit.project-config/v1",
          version: this.#appVersion,
        },
      },
      {
        path: ".agent-devkit/agent-devkit.lock",
        content: {
          schema: "agent-devkit.project-lock/v1",
          version: this.#appVersion,
        },
      },
    ];
  }

  invoke(options: InitServiceOptions): Promise<Result<AgentDevKitErrorCode, ProjectInitResult>> {
    return this.execute(options);
  }
}
