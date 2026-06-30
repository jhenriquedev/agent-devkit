import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { PreferencesRepository } from "./preferences.repository";
import { PreferencesService } from "./preferences.service";

describe("user.preferences", () => {
  it("loads default preferences with seven themes and five languages", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-user-preferences-"));

    try {
      const service = new PreferencesService({
        repository: new PreferencesRepository({ homeDirectory: root }),
      });

      const result = await service.execute({ action: "view" });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap().preferences.theme).toBe("default-purple");
      expect(result.unwrap().preferences.language).toBe("pt-BR");
      expect(result.unwrap().preferences.logRetentionDays).toBe(30);
      expect(result.unwrap().themes).toHaveLength(7);
      expect(result.unwrap().languages.map((language) => language.id)).toEqual([
        "pt-BR",
        "en-US",
        "fr-FR",
        "zh-CN",
        "ja-JP",
      ]);
      expect(result.unwrap().themes[0]).toMatchObject({
        id: "default-purple",
        selected: true,
      });
      expect(result.unwrap().languages[0]).toMatchObject({
        id: "pt-BR",
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

  it("persists selected language in global user preferences", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-user-preferences-"));
    const repository = new PreferencesRepository({ homeDirectory: root });
    const service = new PreferencesService({ repository });

    try {
      const update = await service.execute({ action: "set-language", language: "ja-JP" });
      const view = await service.execute({ action: "view" });

      expect(update.isOk()).toBe(true);
      expect(view.isOk()).toBe(true);
      expect(update.unwrap().preferences.language).toBe("ja-JP");
      expect(view.unwrap().preferences.language).toBe("ja-JP");
      expect(view.unwrap().languages.find((language) => language.id === "ja-JP")).toMatchObject({
        selected: true,
      });
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("persists selected log retention in global user preferences", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-user-preferences-"));
    const repository = new PreferencesRepository({ homeDirectory: root });
    const service = new PreferencesService({ repository });

    try {
      const update = await service.execute({ action: "set-log-retention", logRetentionDays: 90 });
      const view = await service.execute({ action: "view" });

      expect(update.isOk()).toBe(true);
      expect(view.isOk()).toBe(true);
      expect(update.unwrap().preferences.logRetentionDays).toBe(90);
      expect(view.unwrap().preferences.logRetentionDays).toBe(90);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("restores default user preferences", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-user-preferences-"));
    const repository = new PreferencesRepository({ homeDirectory: root });
    const service = new PreferencesService({ repository });

    try {
      await service.execute({ action: "set-theme", theme: "forest-teal" });
      await service.execute({ action: "set-language", language: "en-US" });
      await service.execute({ action: "set-log-retention", logRetentionDays: 90 });

      const reset = await service.execute({ action: "reset-defaults" });

      expect(reset.isOk()).toBe(true);
      expect(reset.unwrap().status).toBe("reset");
      expect(reset.unwrap().preferences).toMatchObject({
        theme: "default-purple",
        language: "pt-BR",
        logRetentionDays: 30,
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
