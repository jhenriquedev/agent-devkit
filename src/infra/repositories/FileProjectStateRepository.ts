import { access, mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import type { ProjectInitFile } from "../../domain/entities/ProjectInitResult";
import type { ProjectStateRepository } from "../../domain/ports/ProjectStateRepository";

export class FileProjectStateRepository implements ProjectStateRepository {
  async existingFiles(projectRoot: string, files: string[]): Promise<string[]> {
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

    return checks.filter((file): file is string => file !== undefined);
  }

  async writeFiles(projectRoot: string, files: ProjectInitFile[]): Promise<void> {
    for (const file of files) {
      const target = join(projectRoot, file.path);
      await mkdir(dirname(target), { recursive: true });
      await writeFile(target, `${JSON.stringify(file.content, null, 2)}\n`, { flag: "wx" });
    }
  }
}
