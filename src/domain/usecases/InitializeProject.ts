import type { ProjectInitFile, ProjectInitResult } from "../entities/ProjectInitResult";
import type { ProjectStateRepository } from "../ports/ProjectStateRepository";

type InitializeProjectDependencies = {
  appVersion: string;
  projectRoot: string;
  repository: ProjectStateRepository;
};

type InitializeProjectOptions = {
  dryRun: boolean;
};

const projectFiles = [".agent-devkit/config.json", ".agent-devkit/agent-devkit.lock"];

export class InitializeProject {
  readonly #appVersion: string;
  readonly #projectRoot: string;
  readonly #repository: ProjectStateRepository;

  constructor(dependencies: InitializeProjectDependencies) {
    this.#appVersion = dependencies.appVersion;
    this.#projectRoot = dependencies.projectRoot;
    this.#repository = dependencies.repository;
  }

  async execute(options: InitializeProjectOptions): Promise<ProjectInitResult> {
    if (options.dryRun) {
      return {
        status: "planned",
        version: this.#appVersion,
        project: {
          root: this.#projectRoot,
        },
        planned: projectFiles,
        created: [],
        skipped: [],
      };
    }

    const skipped = await this.#repository.existingFiles(this.#projectRoot, projectFiles);
    const filesToCreate = this.#files().filter((file) => !skipped.includes(file.path));

    if (filesToCreate.length > 0) {
      await this.#repository.writeFiles(this.#projectRoot, filesToCreate);
    }

    return {
      status: filesToCreate.length > 0 ? "initialized" : "already-initialized",
      version: this.#appVersion,
      project: {
        root: this.#projectRoot,
      },
      planned: projectFiles,
      created: filesToCreate.map((file) => file.path),
      skipped,
    };
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
}
