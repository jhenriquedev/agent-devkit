import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { SurfaceLoader } from "./surface_loader";

describe("SurfaceLoader", () => {
  it("rejects surface files outside the minimum schema", async () => {
    const directory = await mkdtemp(join(tmpdir(), "agent-devkit-surface-"));

    try {
      await writeFile(join(directory, "skill.json"), JSON.stringify({ moduleId: "broken" }));
      const loader = new SurfaceLoader(directory);
      const result = await loader.skill();

      expect(result.isErr()).toBe(true);
    } finally {
      await rm(directory, { force: true, recursive: true });
    }
  });
});
