import { access } from "node:fs/promises";
import type { PathInspector } from "../../domain/ports/PathInspector";

export class NodePathInspector implements PathInspector {
  async exists(path: string): Promise<boolean> {
    try {
      await access(path);
      return true;
    } catch {
      return false;
    }
  }
}
