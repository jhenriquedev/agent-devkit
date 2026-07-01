import { join } from "node:path";
import {
  BaseCapabilityService,
  type CapabilityExecution,
  defineCapabilityConfig,
} from "../../../../infra/bases/capability";
import type { AgentDevKitErrorCode } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import { DoctorInputSchema, type DoctorReport, DoctorReportSchema } from "./doctor.entities";
import type { DoctorRepositoryPort } from "./doctor.repository";

type DoctorServiceDependencies = {
  appVersion: string;
  repository: DoctorRepositoryPort;
};

export const doctorCapabilityConfig = defineCapabilityConfig({
  id: "project.doctor",
  moduleId: "project",
  name: "Doctor",
  description: "Inspect the local Agent DevKit environment without changing state.",
  kind: "deterministic",
  risk: "read-only",
} as const);

export class DoctorService
  extends BaseCapabilityService<typeof doctorCapabilityConfig, DoctorServiceDependencies>
  implements CapabilityExecution<void, DoctorReport>
{
  readonly inputSchema = DoctorInputSchema;
  readonly outputSchema = DoctorReportSchema;
  readonly #appVersion: string;
  readonly #repository: DoctorRepositoryPort;

  constructor(dependencies: DoctorServiceDependencies) {
    super(doctorCapabilityConfig, dependencies);
    this.#appVersion = dependencies.appVersion;
    this.#repository = dependencies.repository;
  }

  async execute(): Promise<Result<AgentDevKitErrorCode, DoctorReport>> {
    const homeDirectory = this.#repository.homeDirectory();
    const cwd = this.#repository.cwd();
    const nodeVersion = this.#repository.nodeVersion();
    const platform = this.#repository.platform();
    const stdinIsTTY = this.#repository.stdinIsTTY();
    const stdoutIsTTY = this.#repository.stdoutIsTTY();

    for (const result of [homeDirectory, cwd, nodeVersion, platform, stdinIsTTY, stdoutIsTTY]) {
      if (result.isErr()) {
        return Result.fail(result.unwrapError());
      }
    }

    const globalStatePath = join(homeDirectory.unwrap(), ".agent-devkit");
    const projectStatePath = join(cwd.unwrap(), ".agent-devkit");
    const globalStateExists = await this.#repository.exists(globalStatePath);
    const projectStateExists = await this.#repository.exists(projectStatePath);

    if (globalStateExists.isErr()) {
      return Result.fail(globalStateExists.unwrapError());
    }

    if (projectStateExists.isErr()) {
      return Result.fail(projectStateExists.unwrapError());
    }

    let models: DoctorReport["models"];

    if (this.#repository.installedModels !== undefined) {
      const installedModels = await this.#repository.installedModels(homeDirectory.unwrap());

      if (installedModels.isErr()) {
        return Result.fail(installedModels.unwrapError());
      }

      models = {
        directory: installedModels.unwrap().directory,
        installed: installedModels.unwrap().ids.length,
        ids: installedModels.unwrap().ids,
      };
    }

    return Result.ok({
      status: globalStateExists.unwrap() || projectStateExists.unwrap() ? "ok" : "warning",
      version: this.#appVersion,
      node: {
        version: nodeVersion.unwrap(),
      },
      system: {
        platform: platform.unwrap(),
        cwd: cwd.unwrap(),
      },
      terminal: {
        stdinIsTTY: stdinIsTTY.unwrap(),
        stdoutIsTTY: stdoutIsTTY.unwrap(),
      },
      runtime: {
        globalState: {
          path: globalStatePath,
          exists: globalStateExists.unwrap(),
        },
        projectState: {
          path: projectStatePath,
          exists: projectStateExists.unwrap(),
        },
      },
      models,
    });
  }

  invoke(): Promise<Result<AgentDevKitErrorCode, DoctorReport>> {
    return this.execute();
  }
}
