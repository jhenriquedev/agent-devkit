import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { PreferencesRepository } from "./preferences.repository";
import { PreferencesService } from "./preferences.service";

describe("user.preferences", () => {
  it("loads default preferences with seven available themes", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-user-preferences-"));

    try {
      const service = new PreferencesService({
        repository: new PreferencesRepository({ homeDirectory: root }),
      });

      const result = await service.execute({ action: "view" });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap().preferences.theme).toBe("default-purple");
      expect(result.unwrap().themes).toHaveLength(7);
      expect(result.unwrap().themes[0]).toMatchObject({
        id: "default-purple",
        selected: true,
      });
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("persists selected theme in global user preferences", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-user-preferences-"));
    const repository = new PreferencesRepository({ homeDirectory: root });
    const service = new PreferencesService({ repository });

    try {
      const update = await service.execute({ action: "set-theme", theme: "forest-teal" });
      const view = await service.execute({ action: "view" });

      expect(update.isOk()).toBe(true);
      expect(view.isOk()).toBe(true);
      expect(update.unwrap().preferences.theme).toBe("forest-teal");
      expect(view.unwrap().preferences.theme).toBe("forest-teal");
      expect(view.unwrap().themes.find((theme) => theme.id === "forest-teal")).toMatchObject({
        selected: true,
      });
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("rejects unknown themes without writing preferences", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-user-preferences-"));
    const service = new PreferencesService({
      repository: new PreferencesRepository({ homeDirectory: root }),
    });

    try {
      const result = await service.execute({ action: "set-theme", theme: "missing-theme" });

      expect(result.isErr()).toBe(true);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });
});
