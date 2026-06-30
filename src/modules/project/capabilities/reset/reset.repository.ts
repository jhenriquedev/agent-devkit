import { access, rm } from "node:fs/promises";
import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import type { AgentDevKitErrorCode } from "../../../../infra/bases/errors";
import { ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";

export interface ResetRepositoryPort extends CapabilityRepositoryPort {
  exists(path: string): Promise<Result<AgentDevKitErrorCode, boolean>>;
  remove(path: string): Promise<Result<AgentDevKitErrorCode, void>>;
}

export class ResetRepository implements ResetRepositoryPort {
  readonly repositoryId = "project.reset.repository";

  async exists(path: string): Promise<Result<AgentDevKitErrorCode, boolean>> {
    try {
      await access(path);
      return Result.ok(true);
    } catch {
      return Result.ok(false);
    }
  }

  async remove(path: string): Promise<Result<AgentDevKitErrorCode, void>> {
    try {
      await rm(path, { force: true, recursive: true });
      return Result.ok(undefined);
    } catch {
      return Result.fail(ErrorCodes.StateResetFailed);
    }
  }
}
