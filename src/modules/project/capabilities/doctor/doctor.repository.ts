import { access } from "node:fs/promises";
import { homedir, platform } from "node:os";
import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import type { AgentDevKitErrorCode } from "../../../../infra/bases/errors";
import { ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";

export interface DoctorRepositoryPort extends CapabilityRepositoryPort {
  cwd(): Result<AgentDevKitErrorCode, string>;
  exists(path: string): Promise<Result<AgentDevKitErrorCode, boolean>>;
  homeDirectory(): Result<AgentDevKitErrorCode, string>;
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

export function doctorRepositoryError(): Result<AgentDevKitErrorCode, never> {
  return Result.fail(ErrorCodes.CapabilityExecutionFailed);
}
