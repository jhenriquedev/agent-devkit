import { BaseCapabilityService, defineCapabilityConfig } from "../../../../infra/bases/capability";
import type { CharacterDefinition, CharacterId } from "../../../../infra/bases/character";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import type {
  PersonalizationResult,
  PersonalizationServiceOptions,
  UserPersonalizationState,
} from "./personalization.entities";
import {
  PersonalizationResultSchema,
  PersonalizationServiceOptionsSchema,
} from "./personalization.entities";
import type { PersonalizationRepositoryPort } from "./personalization.repository";

type PersonalizationServiceDependencies = {
  repository: PersonalizationRepositoryPort;
};

export const personalizationCapabilityConfig = defineCapabilityConfig({
  id: "user.personalization",
  moduleId: "user",
  name: "Agent personalization",
  description: "Read and update the local agent identity, behavior, tone and detail level.",
  kind: "deterministic",
  risk: "writes-global-state",
} as const);

export class PersonalizationService extends BaseCapabilityService<
  typeof personalizationCapabilityConfig,
  PersonalizationServiceDependencies,
  PersonalizationServiceOptions,
  PersonalizationResult
> {
  readonly inputSchema = PersonalizationServiceOptionsSchema;
  readonly outputSchema = PersonalizationResultSchema;
  readonly #repository: PersonalizationRepositoryPort;

  constructor(dependencies: PersonalizationServiceDependencies) {
    super(personalizationCapabilityConfig, dependencies);
    this.#repository = dependencies.repository;
  }

  async execute(
    options: PersonalizationServiceOptions,
  ): Promise<Result<AgentDevKitErrorCode, PersonalizationResult>> {
    const parsedOptions = PersonalizationServiceOptionsSchema.safeParse(options);

    if (!parsedOptions.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const input = parsedOptions.data;
    const existing = await this.#repository.loadProfile();

    if (existing.isErr()) {
      return Result.fail(existing.unwrapError());
    }

    let profile = existing.unwrap();
    let status: PersonalizationResult["status"] = "view";

    if (input.action === "select-preset") {
      const preset = await this.#repository.loadPresetCharacter(input.characterId);

      if (preset.isErr()) {
        return Result.fail(preset.unwrapError());
      }

      profile = this.#stateFromCharacter(preset.unwrap(), preset.unwrap().id);
      status = "preset-selected";
    }

    if (input.action === "update" && input.profile.characterId !== undefined) {
      const preset = await this.#repository.loadPresetCharacter(input.profile.characterId);

      if (preset.isErr()) {
        return Result.fail(preset.unwrapError());
      }

      profile = this.#stateFromCharacter(
        this.#mergeCharacter(preset.unwrap(), input.profile),
        preset.unwrap().id,
      );
      status = "updated";
    } else if (input.action === "update-current" || input.action === "update") {
      profile = {
        ...profile,
        currentCharacter: this.#mergeCharacter(profile.currentCharacter, input.profile),
        updatedAt: new Date().toISOString(),
      };
      status = "character-updated";
    }

    if (input.action === "create-character") {
      const character = await this.#createCharacter(input.character);

      if (character.isErr()) {
        return Result.fail(character.unwrapError());
      }

      const save = await this.#repository.saveCustomCharacter(character.unwrap());

      if (save.isErr()) {
        return Result.fail(save.unwrapError());
      }

      profile = this.#stateFromCharacter(
        character.unwrap(),
        input.character.fromCharacterId ?? profile.selectedPresetId,
      );
      status = "character-created";
    }

    if (input.action === "import-sprite") {
      const characters = await this.#repository.loadCharacters(profile.currentCharacter.id);

      if (characters.isErr()) {
        return Result.fail(characters.unwrapError());
      }

      const character = characters.unwrap().find((candidate) => candidate.id === input.characterId);

      if (character === undefined) {
        return Result.fail(ErrorCodes.InvalidInput);
      }

      const imported = await this.#repository.importSprite(input.characterId, input.sourcePath);

      if (imported.isErr()) {
        return Result.fail(imported.unwrapError());
      }

      const { custom, selected, spritePath, ...characterDefinition } = character;
      void custom;
      void selected;
      void spritePath;

      const saveCharacter = await this.#repository.saveCustomCharacter(characterDefinition);

      if (saveCharacter.isErr()) {
        return Result.fail(saveCharacter.unwrapError());
      }

      profile = {
        ...profile,
        currentCharacter:
          profile.currentCharacter.id === character.id
            ? characterDefinition
            : profile.currentCharacter,
        updatedAt: new Date().toISOString(),
      };
      status = "sprite-imported";
    }

    if (input.action === "reset-current") {
      const preset = await this.#repository.loadPresetCharacter(profile.selectedPresetId);

      if (preset.isErr()) {
        return Result.fail(preset.unwrapError());
      }

      profile = this.#stateFromCharacter(preset.unwrap(), preset.unwrap().id);
      status = "reset";
    }

    if (input.action === "reset-defaults") {
      const defaults = await this.#repository.defaultState();

      if (defaults.isErr()) {
        return Result.fail(defaults.unwrapError());
      }

      profile = {
        ...defaults.unwrap(),
        updatedAt: new Date().toISOString(),
      };
      status = "reset";
    }

    if (status !== "view") {
      const save = await this.#repository.saveProfile(profile);

      if (save.isErr()) {
        return Result.fail(save.unwrapError());
      }
    }

    const characters = await this.#repository.loadCharacters(profile.currentCharacter.id);

    if (characters.isErr()) {
      return Result.fail(characters.unwrapError());
    }

    return Result.ok({
      characters: characters.unwrap().filter((character) => character.active),
      path: this.#repository.profilePath(),
      profile,
      status,
    });
  }

  invoke(
    options: PersonalizationServiceOptions,
  ): Promise<Result<AgentDevKitErrorCode, PersonalizationResult>> {
    return this.execute(options);
  }

  async #createCharacter(
    input: Extract<PersonalizationServiceOptions, { action: "create-character" }>["character"],
  ): Promise<Result<AgentDevKitErrorCode, CharacterDefinition>> {
    let base: CharacterDefinition | undefined;

    if (input.fromCharacterId !== undefined) {
      const preset = await this.#repository.loadPresetCharacter(input.fromCharacterId);

      if (preset.isErr()) {
        return Result.fail(preset.unwrapError());
      }

      base = preset.unwrap();
    }

    const defaults = base === undefined ? await this.#repository.defaultState() : undefined;

    if (defaults?.isErr()) {
      return Result.fail(defaults.unwrapError());
    }

    const fallback = base ?? defaults?.unwrap().currentCharacter;

    if (fallback === undefined) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    return Result.ok(
      this.#mergeCharacter(
        {
          ...fallback,
          active: input.active ?? true,
          default: false,
          id: input.id,
          i18n: { ...fallback.i18n },
        },
        input,
        input.name,
      ),
    );
  }

  #mergeCharacter(
    character: CharacterDefinition,
    update: Partial<CharacterDefinition["profile"]> & {
      active?: boolean;
      name?: string;
    },
    name?: string,
  ): CharacterDefinition {
    const nextName = name ?? update.name;

    return {
      ...character,
      active: update.active ?? character.active,
      name: nextName ?? character.name,
      profile: {
        ...character.profile,
        archetype: update.archetype ?? character.profile.archetype,
        behavior: update.behavior ?? character.profile.behavior,
        detailLevel: update.detailLevel ?? character.profile.detailLevel,
        gender: update.gender ?? character.profile.gender,
        tone: update.tone ?? character.profile.tone,
        traits: update.traits === undefined ? character.profile.traits : [...update.traits],
      },
    };
  }

  #stateFromCharacter(
    character: CharacterDefinition,
    selectedPresetId: CharacterId,
  ): UserPersonalizationState {
    return {
      schema: "agent-devkit.agent-personalization/v2",
      currentCharacter: {
        ...character,
        i18n: { ...character.i18n },
        profile: { ...character.profile, traits: [...character.profile.traits] },
      },
      selectedPresetId,
      updatedAt: new Date().toISOString(),
    };
  }
}
