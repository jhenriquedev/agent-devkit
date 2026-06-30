import { access, rm } from "node:fs/promises";
import type { StateResetRepository } from "../../domain/ports/StateResetRepository";

export class FileStateResetRepository implements StateResetRepository {
  async exists(path: string): Promise<boolean> {
    try {
      await access(path);
      return true;
    } catch {
      return false;
    }
  }

  async remove(path: string): Promise<void> {
    await rm(path, { force: true, recursive: true });
  }
}
