import type { LogCategorySelection } from "../../modules/logs/logs.index";

export type JsonCommandOptions = {
  json?: boolean;
};

export type LogCategoryCommandOptions = {
  all?: boolean;
  technical?: boolean;
};

export function wantsJson(options?: JsonCommandOptions, argv: string[] = process.argv): boolean {
  return options?.json === true || argv.includes("--json");
}

export function parseNonNegativeInteger(value: string | undefined): number | undefined {
  if (value === undefined) {
    return undefined;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isInteger(parsed) && parsed >= 0 && String(parsed) === value.trim()
    ? parsed
    : undefined;
}

export function parsePositiveInteger(value: string): number {
  const parsed = Number.parseInt(value, 10);

  if (!Number.isInteger(parsed) || parsed < 1 || String(parsed) !== value.trim()) {
    throw new Error(`Expected a positive integer, received: ${value}`);
  }

  return parsed;
}

export function logCategoryFromOptions(
  options: LogCategoryCommandOptions,
  argv: string[] = process.argv,
): LogCategorySelection | undefined {
  if (options.all === true || argv.includes("--all")) {
    return "all";
  }

  if (options.technical === true || argv.includes("--technical")) {
    return "technical";
  }

  return undefined;
}
