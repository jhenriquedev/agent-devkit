import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import { PersonalizationRepository } from "./personalization.repository";
import { PersonalizationService } from "./personalization.service";

async function service(homeDirectory: string) {
  return new PersonalizationService({
    repository: new PersonalizationRepository({ homeDirectory }),
  });
}

describe("PersonalizationService", () => {
  it("loads packaged characters with local sprites and translated labels", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-personalization-"));

    try {
      const result = await (await service(home)).execute({ action: "list-characters" });
      const languages = await new I18nCatalog().loadLanguages();

      expect(result.isOk()).toBe(true);
      expect(languages.isOk()).toBe(true);

      for (const character of result.unwrap().characters) {
        expect(character.spritePath).toContain(join("characters", character.id, "sprite."));

        for (const language of languages.unwrap()) {
          expect(language.messages[character.i18n.nameKey]).toEqual(expect.any(String));
          expect(language.messages[character.i18n.taglineKey]).toEqual(expect.any(String));
          expect(language.messages[character.i18n.descriptionKey]).toEqual(expect.any(String));
        }
      }
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("returns the default local agent profile", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-personalization-"));

    try {
      const result = await (await service(home)).execute({ action: "view" });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        characters: expect.arrayContaining([
          expect.objectContaining({
            id: "yuki",
            profile: expect.objectContaining({
              behavior: "pragmatic",
              detailLevel: "technical",
              tone: "formal",
            }),
          }),
        ]),
        profile: {
          currentCharacter: {
            id: "kit",
            profile: {
              behavior: "balanced",
              detailLevel: "concise",
              tone: "direct",
            },
          },
        },
        status: "view",
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("updates and persists the local agent profile", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-personalization-"));

    try {
      const capability = await service(home);
      const result = await capability.execute({
        action: "update",
        profile: {
          name: "Robot",
          behavior: "pragmatic",
          characterId: "robot",
          detailLevel: "technical",
          tone: "neutral",
          traits: ["technical", "precise"],
        },
      });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        profile: {
          currentCharacter: {
            id: "robot",
            name: "Robot",
            profile: {
              traits: ["technical", "precise"],
            },
          },
        },
        status: "updated",
      });

      const payload = JSON.parse(
        await readFile(
          join(home, ".agent-devkit", "data", "personalization", "profile.json"),
          "utf8",
        ),
      );

      expect(payload).toMatchObject({
        schema: "agent-devkit.agent-personalization/v2",
        currentCharacter: {
          id: "robot",
          name: "Robot",
        },
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("applies the selected character preset when only the character changes", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-personalization-"));

    try {
      const result = await (await service(home)).execute({
        action: "update",
        profile: {
          characterId: "joy",
        },
      });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        profile: {
          currentCharacter: {
            id: "joy",
            profile: {
              behavior: "creative",
              detailLevel: "balanced",
              tone: "friendly",
            },
          },
        },
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("resets the profile to defaults while preserving creation timestamp", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-personalization-"));

    try {
      const capability = await service(home);
      await capability.execute({
        action: "update",
        profile: { characterId: "joy", name: "Nova" },
      });
      const reset = await capability.execute({ action: "reset-defaults" });

      expect(reset.isOk()).toBe(true);
      expect(reset.unwrap()).toMatchObject({
        profile: {
          currentCharacter: {
            id: "kit",
          },
        },
        status: "reset",
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("rejects invalid profile updates before writing global state", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-personalization-"));

    try {
      const capability = await service(home);
      const result = await capability.execute({
        action: "update-current",
        profile: { behavior: "banana" },
      } as never);

      expect(result.isErr()).toBe(true);
      const view = await capability.execute({ action: "view" });

      expect(view.isOk()).toBe(true);
      expect(view.unwrap().profile.currentCharacter.profile.behavior).toBe("balanced");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("imports a sprite for a packaged preset without returning duplicate character ids", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-personalization-"));
    const sprite = join(home, "sprite.js");

    try {
      await writeFile(sprite, "export const sprite = {};\n");
      const result = await (await service(home)).execute({
        action: "import-sprite",
        characterId: "yuki",
        sourcePath: sprite,
      });

      expect(result.isOk()).toBe(true);
      const characters = result.unwrap().characters;
      const yukiCharacters = characters.filter((character) => character.id === "yuki");

      expect(yukiCharacters).toHaveLength(1);
      expect(yukiCharacters[0]).toMatchObject({
        custom: true,
        spritePath: expect.stringContaining(
          join(".agent-devkit", "data", "personalization", "characters", "yuki", "sprite.js"),
        ),
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("resets a custom character to the preset used as its base", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-personalization-"));

    try {
      const capability = await service(home);
      const created = await capability.execute({
        action: "create-character",
        character: {
          fromCharacterId: "yuki",
          id: "my-yuki",
          name: "My Yuki",
        },
      });

      expect(created.isOk()).toBe(true);
      expect(created.unwrap().profile.selectedPresetId).toBe("yuki");

      const reset = await capability.execute({ action: "reset-current" });

      expect(reset.isOk()).toBe(true);
      expect(reset.unwrap().profile.currentCharacter.id).toBe("yuki");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("migrates legacy profile and custom characters into the canonical data directory", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-personalization-"));
    const legacyCharacterDirectory = join(home, ".agent-devkit", "characters", "legacy");
    const legacyProfilePath = join(home, ".agent-devkit", "personalization.json");

    try {
      await mkdir(legacyCharacterDirectory, { recursive: true });
      await writeFile(
        legacyProfilePath,
        JSON.stringify({
          schema: "agent-devkit.agent-personalization/v2",
          currentCharacter: {
            active: true,
            default: false,
            i18n: {
              descriptionKey: "characters.yuki.description",
              nameKey: "characters.yuki.name",
              taglineKey: "characters.yuki.tagline",
            },
            id: "legacy",
            name: "Legacy",
            profile: {
              archetype: "legacy",
              behavior: "pragmatic",
              detailLevel: "technical",
              gender: "female",
              tone: "formal",
              traits: ["legacy"],
            },
            schema: "agent-devkit.character/v1",
          },
          selectedPresetId: "yuki",
          updatedAt: "2026-07-01T00:00:00.000Z",
        }),
      );
      await writeFile(
        join(legacyCharacterDirectory, "character.json"),
        JSON.stringify({
          schema: "agent-devkit.character/v1",
          id: "legacy",
          active: true,
          default: false,
          i18n: {
            descriptionKey: "characters.yuki.description",
            nameKey: "characters.yuki.name",
            taglineKey: "characters.yuki.tagline",
          },
          name: "Legacy",
          profile: {
            archetype: "legacy",
            behavior: "pragmatic",
            detailLevel: "technical",
            gender: "female",
            tone: "formal",
            traits: ["legacy"],
          },
        }),
      );

      const result = await (await service(home)).execute({ action: "view" });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap().profile.currentCharacter.id).toBe("legacy");
      expect(result.unwrap().characters).toEqual(
        expect.arrayContaining([expect.objectContaining({ custom: true, id: "legacy" })]),
      );
      await expect(
        readFile(join(home, ".agent-devkit", "data", "personalization", "profile.json"), "utf8"),
      ).resolves.toContain("legacy");
      await expect(
        readFile(
          join(
            home,
            ".agent-devkit",
            "data",
            "personalization",
            "characters",
            "legacy",
            "character.json",
          ),
          "utf8",
        ),
      ).resolves.toContain("Legacy");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
