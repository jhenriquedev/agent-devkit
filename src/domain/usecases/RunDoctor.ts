import { join } from "node:path";
import type { DoctorReport } from "../entities/DoctorReport";
import type { PathInspector } from "../ports/PathInspector";
import type { SystemInfoProvider } from "../ports/SystemInfoProvider";

type RunDoctorDependencies = {
  appVersion: string;
  pathInspector: PathInspector;
  systemInfo: SystemInfoProvider;
};

export class RunDoctor {
  readonly #appVersion: string;
  readonly #pathInspector: PathInspector;
  readonly #systemInfo: SystemInfoProvider;

  constructor(dependencies: RunDoctorDependencies) {
    this.#appVersion = dependencies.appVersion;
    this.#pathInspector = dependencies.pathInspector;
    this.#systemInfo = dependencies.systemInfo;
  }

  async execute(): Promise<DoctorReport> {
    const homeDirectory = this.#systemInfo.homeDirectory();
    const cwd = this.#systemInfo.cwd();
    const globalStatePath = join(homeDirectory, ".agent-devkit");
    const projectStatePath = join(cwd, ".agent-devkit");

    const [globalStateExists, projectStateExists] = await Promise.all([
      this.#pathInspector.exists(globalStatePath),
      this.#pathInspector.exists(projectStatePath),
    ]);

    return {
      status: "ok",
      version: this.#appVersion,
      node: {
        version: this.#systemInfo.nodeVersion(),
      },
      system: {
        platform: this.#systemInfo.platform(),
        cwd,
      },
      terminal: {
        stdinIsTTY: this.#systemInfo.stdinIsTTY(),
        stdoutIsTTY: this.#systemInfo.stdoutIsTTY(),
      },
      runtime: {
        globalState: {
          path: globalStatePath,
          exists: globalStateExists,
        },
        projectState: {
          path: projectStatePath,
          exists: projectStateExists,
        },
      },
    };
  }
}
