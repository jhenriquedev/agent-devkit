const redacted = "[redacted]";
const sensitiveKeyPattern = /(api[-_]?key|auth|credential|password|secret|token|value)/i;

function normalizeOptionName(option: string): string {
  return option.replace(/^--?/, "").replace(/-([a-z])/g, (_, char: string) => char.toUpperCase());
}

function isSensitiveKey(key: string, sensitiveKeys: Set<string>): boolean {
  return sensitiveKeys.has(key) || sensitiveKeyPattern.test(key);
}

export function redactArgv(argv: string[], sensitiveOptions: string[] = []): string[] {
  const sensitiveFlags = new Set(sensitiveOptions);
  const output: string[] = [];

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];

    if (token === undefined) {
      continue;
    }

    if (sensitiveFlags.has(token)) {
      output.push(token);
      if (index + 1 < argv.length) {
        output.push(redacted);
        index += 1;
      }
      continue;
    }

    const [flag] = token.split("=");
    if (flag !== undefined && sensitiveFlags.has(flag) && token.includes("=")) {
      output.push(`${flag}=${redacted}`);
      continue;
    }

    output.push(token);
  }

  return output;
}

export function redactUnknown(value: unknown, sensitiveOptionNames: string[] = []): unknown {
  const sensitiveKeys = new Set(sensitiveOptionNames.map(normalizeOptionName));

  if (Array.isArray(value)) {
    return value.map((item) => redactUnknown(item, sensitiveOptionNames));
  }

  if (value === null || typeof value !== "object") {
    return value;
  }

  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>)
      .filter(([, entryValue]) => entryValue !== undefined && typeof entryValue !== "function")
      .map(([key, entryValue]) => [
        key,
        isSensitiveKey(key, sensitiveKeys)
          ? redacted
          : redactUnknown(entryValue, sensitiveOptionNames),
      ]),
  );
}

export function redactRecord(
  value: Record<string, unknown>,
  sensitiveOptionNames: string[] = [],
): Record<string, unknown> {
  return redactUnknown(value, sensitiveOptionNames) as Record<string, unknown>;
}
