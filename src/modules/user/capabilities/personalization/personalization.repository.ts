import { existsSync } from "node:fs";
import { access, copyFile, mkdir, readdir, readFile } from "node:fs/promises";
import { homedir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import {
  type CharacterDefinition,
  CharacterDefinitionSchema,
  type CharacterId,
} from "../../../../infra/bases/character";
import type { AgentDataStore } from "../../../../infra/bases/data_store";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import { LocalAgentDataStore } from "../../../../infra/data/local_agent_data_store";
import {
  type CharacterListItem,
  type UserPersonalizationState,
  UserPersonalizationStateSchema,
} from "./personalization.entities";

export type PersonalizationRepositoryOptions = {
  assetsDirectory?: string;
  dataStore?: AgentDataStore;
  homeDirectory?: string;
};

export interface PersonalizationRepositoryPort extends CapabilityRepositoryPort {
  charactersDirectory(): string;
  customCharactersDirectory(): string;
  defaultState(): Promise<Result<AgentDevKitErrorCode, UserPersonalizationState>>;
  importSprite(
    characterId: CharacterId,
    sourcePath: string,
  ): Promise<Result<AgentDevKitErrorCode, string>>;
  loadCharacters(
    selectedCharacterId?: CharacterId,
  ): Promise<Result<AgentDevKitErrorCode, CharacterListItem[]>>;
  loadPresetCharacter(
    characterId: CharacterId,
  ): Promise<Result<AgentDevKitErrorCode, CharacterDefinition>>;
  loadProfile(): Promise<Result<AgentDevKitErrorCode, UserPersonalizationState>>;
  profilePath(): string;
  saveCustomCharacter(character: CharacterDefinition): Promise<Result<AgentDevKitErrorCode, void>>;
  saveProfile(profile: UserPersonalizationState): Promise<Result<AgentDevKitErrorCode, void>>;
}

function defaultAssetsDirectory(): string {
  const moduleDirectory = dirname(fileURLToPath(import.meta.url));
  const candidates = [
    resolve(moduleDirectory, "../../../../assets"),
    resolve(moduleDirectory, "../src/assets"),
    resolve(process.cwd(), "src/assets"),
  ];

  return (
    candidates.find((candidate) => existsSync(candidate)) ?? resolve(process.cwd(), "src/assets")
  );
}

function cloneCharacter(character: CharacterDefinition): CharacterDefinition {
  return {
    ...character,
    i18n: { ...character.i18n },
    profile: {
      ...character.profile,
      traits: [...character.profile.traits],
    },
  };
}

export class PersonalizationRepository implements PersonalizationRepositoryPort {
  readonly repositoryId = "user.personalization.repository";
  readonly #assetsDirectory: string;
  readonly #dataStore: AgentDataStore;
  readonly #homeDirectory: string;

  constructor(options: PersonalizationRepositoryOptions = {}) {
    this.#assetsDirectory = options.assetsDirectory ?? defaultAssetsDirectory();
    this.#homeDirectory = options.homeDirectory ?? homedir();
    this.#dataStore =
      options.dataStore ??
      new LocalAgentDataStore({
        rootDirectory: join(this.#homeDirectory, ".agent-devkit", "data"),
      });
  }

  charactersDirectory(): string {
    return join(this.#assetsDirectory, "characters");
  }

  customCharactersDirectory(): string {
    const resolved = this.#dataStore.resolve({
      namespace: "personalization",
      segments: ["characters"],
    });

    return resolved.isOk()
      ? resolved.unwrap()
      : join(this.#homeDirectory, ".agent-devkit", "data", "personalization", "characters");
  }

  async defaultState(): Promise<Result<AgentDevKitErrorCode, UserPersonalizationState>> {
    const characters = await this.#loadPresetCharacters();

    if (characters.isErr()) {
      return Result.fail(characters.unwrapError());
    }

    const defaultCharacter =
      characters.unwrap().find((character) => character.default && character.active) ??
      characters.unwrap().find((character) => character.id === "kit" && character.active);

    if (defaultCharacter === undefined) {
      return Result.fail(ErrorCodes.AssetReadFailed);
    }

    return Result.ok({
      schema: "agent-devkit.agent-personalization/v2",
      currentCharacter: cloneCharacter(defaultCharacter),
      selectedPresetId: defaultCharacter.id,
      updatedAt: new Date(0).toISOString(),
    });
  }

  async importSprite(
    characterId: CharacterId,
    sourcePath: string,
  ): Promise<Result<AgentDevKitErrorCode, string>> {
    try {
      await access(sourcePath);
      const extension = basename(sourcePath).includes(".")
        ? `.${basename(sourcePath).split(".").pop() ?? "sprite"}`
        : "";
      const targetDirectory = join(this.customCharactersDirectory(), characterId);
      const targetPath = join(targetDirectory, `sprite${extension}`);

      await mkdir(targetDirectory, { recursive: true });
      await copyFile(sourcePath, targetPath);

      return Result.ok(targetPath);
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }

  async loadCharacters(
    selectedCharacterId?: CharacterId,
  ): Promise<Result<AgentDevKitErrorCode, CharacterListItem[]>> {
    const presets = await this.#loadPresetCharacters();
    const custom = await this.#loadCustomCharacters();

    if (presets.isErr()) {
      return Result.fail(presets.unwrapError());
    }

    if (custom.isErr()) {
      return Result.fail(custom.unwrapError());
    }

    const charactersById = new Map<string, CharacterListItem>();

    for (const character of presets.unwrap()) {
      charactersById.set(character.id, this.#listItem(character, false, selectedCharacterId));
    }

    for (const character of custom.unwrap()) {
      charactersById.set(character.id, this.#listItem(character, true, selectedCharacterId));
    }

    return Result.ok([...charactersById.values()]);
  }

  async loadPresetCharacter(
    characterId: CharacterId,
  ): Promise<Result<AgentDevKitErrorCode, CharacterDefinition>> {
    const characters = await this.#loadPresetCharacters();

    if (characters.isErr()) {
      return Result.fail(characters.unwrapError());
    }

    const character = characters
      .unwrap()
      .find((candidate) => candidate.id === characterId && candidate.active);

    return character === undefined
      ? Result.fail(ErrorCodes.InvalidInput)
      : Result.ok(cloneCharacter(character));
  }

  async loadProfile(): Promise<Result<AgentDevKitErrorCode, UserPersonalizationState>> {
    const path = { namespace: "personalization" as const, segments: ["profile.json"] };
    const exists = await this.#dataStore.exists(path);

    if (exists.isErr()) {
      return Result.fail(exists.unwrapError());
    }

    if (exists.unwrap()) {
      const payload = await this.#dataStore.readJson<unknown>(path);

      if (payload.isErr()) {
        return Result.fail(payload.unwrapError());
      }

      const parsed = UserPersonalizationStateSchema.safeParse(payload.unwrap());

      return parsed.success ? Result.ok(parsed.data) : Result.fail(ErrorCodes.InvalidInput);
    }

    const legacy = await this.#loadLegacyProfile();

    if (legacy.isOk()) {
      await this.saveProfile(legacy.unwrap());
      return legacy;
    }

    if (legacy.unwrapError() !== ErrorCodes.FileReadFailed) {
      return Result.fail(legacy.unwrapError());
    }

    return this.defaultState();
  }

  async #loadLegacyProfile(): Promise<Result<AgentDevKitErrorCode, UserPersonalizationState>> {
    try {
      await access(this.#legacyProfilePath());
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }

    try {
      const payload = JSON.parse(await readFile(this.#legacyProfilePath(), "utf8"));
      const parsed = UserPersonalizationStateSchema.safeParse(payload);

      if (!parsed.success) {
        return Result.fail(ErrorCodes.InvalidInput);
      }

      return Result.ok(parsed.data);
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  profilePath(): string {
    const resolved = this.#dataStore.resolve({
      namespace: "personalization",
      segments: ["profile.json"],
    });

    return resolved.isOk()
      ? resolved.unwrap()
      : join(this.#homeDirectory, ".agent-devkit", "data", "personalization", "profile.json");
  }

  async saveCustomCharacter(
    character: CharacterDefinition,
  ): Promise<Result<AgentDevKitErrorCode, void>> {
    try {
      return await this.#dataStore.writeJson(
        { namespace: "personalization", segments: ["characters", character.id, "character.json"] },
        character,
      );
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }

  async saveProfile(
    profile: UserPersonalizationState,
  ): Promise<Result<AgentDevKitErrorCode, void>> {
    try {
      return await this.#dataStore.writeJson(
        { namespace: "personalization", segments: ["profile.json"] },
        profile,
      );
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }

  async #loadCustomCharacters(): Promise<Result<AgentDevKitErrorCode, CharacterDefinition[]>> {
    const legacy = await this.#loadLegacyCustomCharacters();

    if (legacy.isOk()) {
      for (const character of legacy.unwrap()) {
        await this.saveCustomCharacter(character);
        await this.#migrateLegacySprite(character.id);
      }
    } else if (legacy.unwrapError() !== ErrorCodes.FileReadFailed) {
      return Result.fail(legacy.unwrapError());
    }

    try {
      await access(this.customCharactersDirectory());
    } catch {
      return Result.ok([]);
    }

    return this.#loadCharactersFromDirectory(this.customCharactersDirectory());
  }

  async #loadPresetCharacters(): Promise<Result<AgentDevKitErrorCode, CharacterDefinition[]>> {
    return this.#loadCharactersFromDirectory(this.charactersDirectory());
  }

  async #loadCharactersFromDirectory(
    directory: string,
  ): Promise<Result<AgentDevKitErrorCode, CharacterDefinition[]>> {
    try {
      const entries = (await readdir(directory, { withFileTypes: true }))
        .filter((entry) => entry.isDirectory())
        .map((entry) => entry.name)
        .sort((left, right) => left.localeCompare(right));
      const characters: CharacterDefinition[] = [];

      for (const entry of entries) {
        const payload = JSON.parse(
          await readFile(join(directory, entry, "character.json"), "utf8"),
        );
        const parsed = CharacterDefinitionSchema.safeParse(payload);

        if (!parsed.success) {
          return Result.fail(ErrorCodes.InvalidInput);
        }

        characters.push(parsed.data);
      }

      return Result.ok(characters);
    } catch {
      return Result.fail(ErrorCodes.AssetReadFailed);
    }
  }

  #listItem(
    character: CharacterDefinition,
    custom: boolean,
    selectedCharacterId?: CharacterId,
  ): CharacterListItem {
    const packageSpritePath = this.#findPackageCharacterSprite(character.id);
    const userSpritePath = this.#findUserCharacterSprite(character.id);

    return {
      ...cloneCharacter(character),
      custom,
      selected: character.id === selectedCharacterId,
      spritePath:
        userSpritePath !== undefined
          ? userSpritePath
          : packageSpritePath !== undefined
            ? packageSpritePath
            : undefined,
    };
  }

  #findPackageCharacterSprite(characterId: CharacterId): string | undefined {
    const directory = join(this.charactersDirectory(), characterId);
    const candidates = ["sprite.js", "sprite.svg", "sprite.png", "sprite.jpg", "sprite.jpeg"];

    return candidates
      .map((candidate) => join(directory, candidate))
      .find((candidate) => existsSync(candidate));
  }

  #findUserCharacterSprite(characterId: CharacterId): string | undefined {
    const directory = join(this.customCharactersDirectory(), characterId);

    if (!existsSync(directory)) {
      return undefined;
    }

    const candidates = ["sprite.js", "sprite.svg", "sprite.png", "sprite.jpg", "sprite.jpeg"];

    return candidates
      .map((candidate) => join(directory, candidate))
      .find((candidate) => existsSync(candidate));
  }

  async #loadLegacyCustomCharacters(): Promise<
    Result<AgentDevKitErrorCode, CharacterDefinition[]>
  > {
    try {
      await access(this.#legacyCustomCharactersDirectory());
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }

    return this.#loadCharactersFromDirectory(this.#legacyCustomCharactersDirectory());
  }

  async #migrateLegacySprite(characterId: CharacterId): Promise<void> {
    const source = ["sprite.js", "sprite.svg", "sprite.png", "sprite.jpg", "sprite.jpeg"]
      .map((candidate) => join(this.#legacyCustomCharactersDirectory(), characterId, candidate))
      .find((candidate) => existsSync(candidate));

    if (source === undefined) {
      return;
    }

    const extension = basename(source).includes(".")
      ? `.${basename(source).split(".").pop() ?? "sprite"}`
      : "";
    const target = this.#dataStore.resolve({
      namespace: "personalization",
      segments: ["characters", characterId, `sprite${extension}`],
    });

    if (target.isErr()) {
      return;
    }

    await mkdir(dirname(target.unwrap()), { recursive: true });
    await copyFile(source, target.unwrap()).catch(() => undefined);
  }

  #legacyCustomCharactersDirectory(): string {
    return join(this.#homeDirectory, ".agent-devkit", "characters");
  }

  #legacyProfilePath(): string {
    return join(this.#homeDirectory, ".agent-devkit", "personalization.json");
  }
}
