import { access, readdir } from "node:fs/promises";
import { homedir, platform } from "node:os";
import { basename, join } from "node:path";
import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";

export type DoctorInstalledModels = {
  directory: string;
  ids: string[];
};

export interface DoctorRepositoryPort extends CapabilityRepositoryPort {
  cwd(): Result<AgentDevKitErrorCode, string>;
  exists(path: string): Promise<Result<AgentDevKitErrorCode, boolean>>;
  homeDirectory(): Result<AgentDevKitErrorCode, string>;
  installedModels?(
    homeDirectory: string,
  ): Promise<Result<AgentDevKitErrorCode, DoctorInstalledModels>>;
  nodeVersion(): Result<AgentDevKitErrorCode, string>;
  platform(): Result<AgentDevKitErrorCode, string>;
  stdinIsTTY(): Result<AgentDevKitErrorCode, boolean>;
  stdoutIsTTY(): Result<AgentDevKitErrorCode, boolean>;
}

export class DoctorRepository implements DoctorRepositoryPort {
  readonly repositoryId = "project.doctor.repository";

  cwd(): Result<AgentDevKitErrorCode, string> {
    return Result.ok(process.cwd());
  }

  async exists(path: string): Promise<Result<AgentDevKitErrorCode, boolean>> {
    try {
      await access(path);
      return Result.ok(true);
    } catch {
      return Result.ok(false);
    }
  }

  homeDirectory(): Result<AgentDevKitErrorCode, string> {
    return Result.ok(homedir());
  }

  async installedModels(
    homeDirectory: string,
  ): Promise<Result<AgentDevKitErrorCode, DoctorInstalledModels>> {
    const directory = join(homeDirectory, ".agent-devkit", "models");

    try {
      const files = await readdir(directory);
      return Result.ok({
        directory,
        ids: files
          .filter((file) => file.endsWith(".gguf"))
          .map((file) => basename(file, ".gguf"))
          .sort(),
      });
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") {
        return Result.ok({ directory, ids: [] });
      }

      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  nodeVersion(): Result<AgentDevKitErrorCode, string> {
    return Result.ok(process.version);
  }

  platform(): Result<AgentDevKitErrorCode, string> {
    return Result.ok(platform());
  }

  stdinIsTTY(): Result<AgentDevKitErrorCode, boolean> {
    return Result.ok(process.stdin.isTTY === true);
  }

  stdoutIsTTY(): Result<AgentDevKitErrorCode, boolean> {
    return Result.ok(process.stdout.isTTY === true);
  }
}
