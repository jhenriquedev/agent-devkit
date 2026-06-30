import type { ProjectInitFile } from "../entities/ProjectInitResult";

export type ProjectStateRepository = {
  existingFiles(projectRoot: string, files: string[]): Promise<string[]>;
  writeFiles(projectRoot: string, files: ProjectInitFile[]): Promise<void>;
};
