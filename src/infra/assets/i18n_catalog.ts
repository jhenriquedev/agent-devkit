import { existsSync, readdirSync, readFileSync } from "node:fs";
import { readdir, readFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import {
  type LanguageDefinition,
  LanguageDefinitionSchema,
  type LanguageId,
  type Translator,
} from "../bases/i18n";
import { Result } from "../bases/result";

export type I18nCatalogOptions = {
  directory?: string;
  fallbackLanguage?: LanguageId;
};

const languageOrder: LanguageId[] = ["pt-BR", "en-US", "fr-FR", "zh-CN", "ja-JP"];

function defaultI18nDirectory(): string {
  const moduleDirectory = dirname(fileURLToPath(import.meta.url));
  const candidates = [
    resolve(moduleDirectory, "../../assets/i18n"),
    resolve(moduleDirectory, "../src/assets/i18n"),
    resolve(process.cwd(), "src/assets/i18n"),
  ];

  return (
    candidates.find((candidate) => existsSync(candidate)) ??
    resolve(process.cwd(), "src/assets/i18n")
  );
}

function sortLanguages(languages: LanguageDefinition[]): LanguageDefinition[] {
  return languages.sort(
    (left, right) => languageOrder.indexOf(left.id) - languageOrder.indexOf(right.id),
  );
}

function interpolate(value: string, variables: Record<string, string | number | boolean>): string {
  return value.replaceAll(/\{\{([a-zA-Z0-9_.-]+)\}\}/g, (_, key: string) =>
    variables[key] === undefined ? `{{${key}}}` : String(variables[key]),
  );
}

export class I18nCatalog {
  readonly #directory: string;
  readonly #fallbackLanguage: LanguageId;
  #languages?: LanguageDefinition[];

  constructor(options: I18nCatalogOptions = {}) {
    this.#directory = options.directory ?? defaultI18nDirectory();
    this.#fallbackLanguage = options.fallbackLanguage ?? "pt-BR";
  }

  async loadLanguages(): Promise<Result<AgentDevKitErrorCode, LanguageDefinition[]>> {
    if (this.#languages !== undefined) {
      return Result.ok(this.#languages);
    }

    try {
      const files = (await readdir(this.#directory)).filter((file) => file.endsWith(".json"));
      const languages: LanguageDefinition[] = [];

      for (const file of files) {
        const parsed = LanguageDefinitionSchema.safeParse(
          JSON.parse(await readFile(join(this.#directory, file), "utf8")),
        );

        if (!parsed.success) {
          return Result.fail(ErrorCodes.InvalidInput);
        }

        languages.push(parsed.data);
      }

      this.#languages = sortLanguages(languages);
      return Result.ok(this.#languages);
    } catch {
      return Result.fail(ErrorCodes.AssetReadFailed);
    }
  }

  loadLanguagesSync(): Result<AgentDevKitErrorCode, LanguageDefinition[]> {
    if (this.#languages !== undefined) {
      return Result.ok(this.#languages);
    }

    try {
      const files = readdirSync(this.#directory).filter((file) => file.endsWith(".json"));
      const languages: LanguageDefinition[] = [];

      for (const file of files) {
        const parsed = LanguageDefinitionSchema.safeParse(
          JSON.parse(readFileSync(join(this.#directory, file), "utf8")),
        );

        if (!parsed.success) {
          return Result.fail(ErrorCodes.InvalidInput);
        }

        languages.push(parsed.data);
      }

      this.#languages = sortLanguages(languages);
      return Result.ok(this.#languages);
    } catch {
      return Result.fail(ErrorCodes.AssetReadFailed);
    }
  }

  async translate(
    language: LanguageId,
    key: string,
    values: Record<string, string | number | boolean> = {},
  ): Promise<Result<AgentDevKitErrorCode, string>> {
    const languages = await this.loadLanguages();

    if (languages.isErr()) {
      return Result.fail(languages.unwrapError());
    }

    return Result.ok(this.#translateFromLanguages(languages.unwrap(), language, key, values));
  }

  translator(language: LanguageId): Translator {
    const languages = this.loadLanguagesSync();

    return {
      language,
      t: (key, values = {}) => {
        if (languages.isErr()) {
          return key;
        }

        return this.#translateFromLanguages(languages.unwrap(), language, key, values);
      },
    };
  }

  #translateFromLanguages(
    languages: LanguageDefinition[],
    language: LanguageId,
    key: string,
    values: Record<string, string | number | boolean>,
  ): string {
    const selected =
      languages.find((candidate) => candidate.id === language) ??
      languages.find((candidate) => candidate.id === this.#fallbackLanguage);
    const fallback = languages.find((candidate) => candidate.id === this.#fallbackLanguage);
    const value = selected?.messages[key] ?? fallback?.messages[key] ?? key;

    return interpolate(value, values);
  }
}
