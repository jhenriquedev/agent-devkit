export type LogLevel = "debug" | "error" | "info" | "warn";

export interface Logger {
  write(level: LogLevel, message: string, metadata?: Record<string, unknown>): void;
}

export class ConsoleLogger implements Logger {
  write(level: LogLevel, message: string, metadata?: Record<string, unknown>): void {
    const payload = metadata ? ` ${JSON.stringify(metadata)}` : "";
    console.error(`[${level}] ${message}${payload}`);
  }
}

export class NullLogger implements Logger {
  write(): void {
    // Intentionally empty.
  }
}
