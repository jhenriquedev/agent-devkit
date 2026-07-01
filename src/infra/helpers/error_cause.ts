export type ErrorCause = {
  code?: string;
  message: string;
  name: string;
};

export function errorCause(error: unknown): ErrorCause {
  if (error instanceof Error) {
    const code =
      typeof (error as NodeJS.ErrnoException).code === "string"
        ? (error as NodeJS.ErrnoException).code
        : undefined;

    return {
      code,
      message: error.message,
      name: error.name,
    };
  }

  return {
    message: String(error),
    name: "Error",
  };
}
