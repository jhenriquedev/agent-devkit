import { z } from "zod";
import {
  CharacterDefinitionSchema,
  CharacterIdSchema,
  CharacterProfileSchema,
} from "../../../../infra/bases/character";

export const UserPersonalizationStateSchema = z
  .object({
    currentCharacter: CharacterDefinitionSchema,
    schema: z.literal("agent-devkit.agent-personalization/v2"),
    selectedPresetId: CharacterIdSchema,
    updatedAt: z.string().min(1),
  })
  .strict();

const CharacterUpdateSchema = CharacterProfileSchema.partial()
  .extend({
    active: z.boolean().optional(),
    name: z.string().min(1).max(80).optional(),
    traits: z.array(z.string().min(1).max(120)).max(20).optional(),
  })
  .strict();

const CreateCharacterSchema = z
  .object({
    active: z.boolean().optional(),
    fromCharacterId: CharacterIdSchema.optional(),
    id: CharacterIdSchema,
    name: z.string().min(1).max(80),
  })
  .merge(CharacterProfileSchema.partial())
  .strict();

export const PersonalizationServiceOptionsSchema = z.discriminatedUnion("action", [
  z.object({ action: z.literal("view") }).strict(),
  z.object({ action: z.literal("list-characters") }).strict(),
  z
    .object({
      action: z.literal("select-preset"),
      characterId: CharacterIdSchema,
    })
    .strict(),
  z
    .object({
      action: z.literal("update-current"),
      profile: CharacterUpdateSchema,
    })
    .strict(),
  z
    .object({
      action: z.literal("create-character"),
      character: CreateCharacterSchema,
    })
    .strict(),
  z
    .object({
      action: z.literal("import-sprite"),
      characterId: CharacterIdSchema,
      sourcePath: z.string().min(1),
    })
    .strict(),
  z.object({ action: z.literal("reset-current") }).strict(),
  z.object({ action: z.literal("reset-defaults") }).strict(),
  z
    .object({
      action: z.literal("update"),
      profile: CharacterUpdateSchema.extend({
        characterId: CharacterIdSchema.optional(),
      }),
    })
    .strict(),
]);

export type UserPersonalizationState = z.infer<typeof UserPersonalizationStateSchema>;
export type PersonalizationServiceOptions = z.infer<typeof PersonalizationServiceOptionsSchema>;
export type PersonalizationStatus =
  | "character-created"
  | "character-updated"
  | "preset-selected"
  | "reset"
  | "sprite-imported"
  | "updated"
  | "view";

export type CharacterListItem = z.infer<typeof CharacterDefinitionSchema> & {
  readonly custom: boolean;
  readonly selected: boolean;
  readonly spritePath?: string;
};

export type PersonalizationResult = {
  characters: CharacterListItem[];
  path: string;
  profile: UserPersonalizationState;
  status: PersonalizationStatus;
};

const CharacterListItemSchema = CharacterDefinitionSchema.extend({
  custom: z.boolean(),
  selected: z.boolean(),
  spritePath: z.string().min(1).optional(),
});

export const PersonalizationResultSchema = z.object({
  characters: z.array(CharacterListItemSchema),
  path: z.string().min(1),
  profile: UserPersonalizationStateSchema,
  status: z.enum([
    "character-created",
    "character-updated",
    "preset-selected",
    "reset",
    "sprite-imported",
    "updated",
    "view",
  ]),
});
