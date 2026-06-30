import { access, mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import type { AgentDevKitErrorCode } from "../../../../infra/bases/errors";
import { ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import type { ProjectInitFile } from "./init.entities";

export interface InitRepositoryPort extends CapabilityRepositoryPort {
  existingFiles(
    projectRoot: string,
    files: string[],
  ): Promise<Result<AgentDevKitErrorCode, string[]>>;
  writeFiles(
    projectRoot: string,
    files: ProjectInitFile[],
  ): Promise<Result<AgentDevKitErrorCode, void>>;
}

export class InitRepository implements InitRepositoryPort {
  readonly repositoryId = "project.init.repository";

  async existingFiles(
    projectRoot: string,
    files: string[],
  ): Promise<Result<AgentDevKitErrorCode, string[]>> {
    try {
      const checks = await Promise.all(
        files.map(async (file) => {
          try {
            await access(join(projectRoot, file));
            return file;
          } catch {
            return undefined;
          }
        }),
      );

      return Result.ok(checks.filter((file): file is string => file !== undefined));
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  async writeFiles(
    projectRoot: string,
    files: ProjectInitFile[],
  ): Promise<Result<AgentDevKitErrorCode, void>> {
    try {
      for (const file of files) {
        const target = join(projectRoot, file.path);
        await mkdir(dirname(target), { recursive: true });
        await writeFile(target, `${JSON.stringify(file.content, null, 2)}\n`, { flag: "wx" });
      }

      return Result.ok(undefined);
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }
}
