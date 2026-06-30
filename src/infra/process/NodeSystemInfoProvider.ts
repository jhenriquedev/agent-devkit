import { homedir, platform } from "node:os";
import type { SystemInfoProvider } from "../../domain/ports/SystemInfoProvider";

export class NodeSystemInfoProvider implements SystemInfoProvider {
  cwd(): string {
    return process.cwd();
  }

  homeDirectory(): string {
    return homedir();
  }

  nodeVersion(): string {
    return process.version;
  }

  platform(): string {
    return platform();
  }

  stdinIsTTY(): boolean {
    return process.stdin.isTTY === true;
  }

  stdoutIsTTY(): boolean {
    return process.stdout.isTTY === true;
  }
}
