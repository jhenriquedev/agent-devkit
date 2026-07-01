import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import type { CharacterDefinition } from "../../../../infra/bases/character";
import type { Translator } from "../../../../infra/bases/i18n";
import type { CharacterListItem, PersonalizationResult } from "./personalization.entities";

const fallbackTranslator = new I18nCatalog().translator("pt-BR");

function characterName(character: CharacterDefinition, translator: Translator): string {
  return character.name ?? translator.t(character.i18n.nameKey);
}

export function formatPersonalizationText(
  result: PersonalizationResult,
  translator: Translator = fallbackTranslator,
): string {
  const current = result.profile.currentCharacter;

  return [
    translator.t("personalization.title"),
    translator.t("personalization.command"),
    "",
    `[${translator.t("personalization.status", { status: result.status })}]`,
    `  ${translator.t("personalization.field.file").padEnd(12)} ${result.path}`,
    `  ${translator.t("personalization.field.name").padEnd(12)} ${characterName(current, translator)}`,
    `  ${translator.t("personalization.field.character").padEnd(12)} ${current.id}`,
    `  ${translator.t("personalization.field.behavior").padEnd(12)} ${current.profile.behavior}`,
    `  ${translator.t("personalization.field.tone").padEnd(12)} ${current.profile.tone}`,
    `  ${translator.t("personalization.field.detail").padEnd(12)} ${current.profile.detailLevel}`,
    `  ${translator.t("personalization.field.traits").padEnd(12)} ${current.profile.traits.join(", ")}`,
    `  ${translator.t("personalization.field.sprite").padEnd(12)} ${current.id}/sprite`,
    "",
    `  ${translator.t("personalization.section.characters")}`,
    ...result.characters.map((character) => formatCharacterLine(character, translator)),
  ].join("\n");
}

function formatCharacterLine(character: CharacterListItem, translator: Translator): string {
  const source = character.custom
    ? translator.t("personalization.label.custom")
    : translator.t("personalization.label.preset");

  return `    ${character.selected ? "*" : " "} ${character.id.padEnd(8)} ${characterName(character, translator).padEnd(10)} ${source} ${character.profile.behavior} / ${character.profile.tone} / ${character.profile.detailLevel}`;
}
