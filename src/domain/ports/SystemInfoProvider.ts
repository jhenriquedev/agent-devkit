export type SystemInfoProvider = {
  cwd(): string;
  homeDirectory(): string;
  nodeVersion(): string;
  platform(): string;
  stdinIsTTY(): boolean;
  stdoutIsTTY(): boolean;
};
