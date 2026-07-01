import { access, chmod, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { basename, delimiter, dirname, join } from "node:path";
import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import type { PreferencesRepositoryPort } from "../preferences/preferences.repository";
import type { CliAliasState } from "./cliAlias.entities";
import { CliAliasNameSchema } from "./cliAlias.entities";

export type CliAliasRepositoryOptions = {
  agentCommand?: string;
  envPath?: string;
  homeDirectory?: string;
  shell?: string;
  preferencesRepository: PreferencesRepositoryPort;
};

export interface CliAliasRepositoryPort extends CapabilityRepositoryPort {
  activationCommand(): string;
  binDirectory(): string;
  binDirectoryInPath(): boolean;
  loadAlias(): Promise<Result<AgentDevKitErrorCode, CliAliasState | undefined>>;
  removeAlias(): Promise<Result<AgentDevKitErrorCode, void>>;
  saveAlias(name: string, force?: boolean): Promise<Result<AgentDevKitErrorCode, CliAliasState>>;
  shellCommand(): string;
  syncAlias(): Promise<Result<AgentDevKitErrorCode, CliAliasState>>;
}

const reservedAliases = new Set([
  "agent",
  "bash",
  "cat",
  "cd",
  "chmod",
  "curl",
  "git",
  "node",
  "npm",
  "npx",
  "rm",
  "sh",
  "sudo",
  "tsx",
  "yarn",
  "zsh",
]);

function now(): string {
  return new Date().toISOString();
}

export class CliAliasRepository implements CliAliasRepositoryPort {
  readonly repositoryId = "user.cli_alias.repository";
  readonly #agentCommand: string;
  readonly #envPath: string;
  readonly #homeDirectory: string;
  readonly #preferencesRepository: PreferencesRepositoryPort;
  readonly #shell: string;

  constructor(options: CliAliasRepositoryOptions) {
    this.#agentCommand = options.agentCommand ?? "agent";
    this.#envPath = options.envPath ?? process.env.PATH ?? "";
    this.#homeDirectory = options.homeDirectory ?? homedir();
    this.#preferencesRepository = options.preferencesRepository;
    this.#shell = options.shell ?? process.env.SHELL ?? "";
  }

  activationCommand(): string {
    return `export PATH="${this.binDirectory()}:$PATH"`;
  }

  binDirectory(): string {
    return join(this.#homeDirectory, ".agent-devkit", "bin");
  }

  binDirectoryInPath(): boolean {
    return this.#envPath.split(delimiter).filter(Boolean).includes(this.binDirectory());
  }

  async loadAlias(): Promise<Result<AgentDevKitErrorCode, CliAliasState | undefined>> {
    const preferences = await this.#preferencesRepository.loadPreferences();

    if (preferences.isErr()) {
      return Result.fail(preferences.unwrapError());
    }

    return Result.ok(preferences.unwrap().cliAlias);
  }

  async removeAlias(): Promise<Result<AgentDevKitErrorCode, void>> {
    const preferences = await this.#preferencesRepository.loadPreferences();

    if (preferences.isErr()) {
      return Result.fail(preferences.unwrapError());
    }

    const alias = preferences.unwrap().cliAlias;

    if (alias !== undefined) {
      await this.#removeManagedShim(alias.shimPath);
    }

    const { cliAlias, ...next } = preferences.unwrap();
    void cliAlias;

    return this.#preferencesRepository.savePreferences({
      ...next,
      updatedAt: now(),
    });
  }

  async saveAlias(
    name: string,
    force = false,
  ): Promise<Result<AgentDevKitErrorCode, CliAliasState>> {
    const validName = this.#validateName(name);

    if (validName.isErr()) {
      return Result.fail(validName.unwrapError());
    }

    const preferences = await this.#preferencesRepository.loadPreferences();

    if (preferences.isErr()) {
      return Result.fail(preferences.unwrapError());
    }

    const alias: CliAliasState = {
      binDirectory: this.binDirectory(),
      enabled: true,
      name: validName.unwrap(),
      shimPath: this.#shimPath(validName.unwrap()),
      updatedAt: now(),
    };
    const collision = await this.#hasUnsafeCollision(alias, force);

    if (collision.isErr()) {
      return Result.fail(collision.unwrapError());
    }

    if (preferences.unwrap().cliAlias?.name !== alias.name) {
      await this.#removeManagedShim(preferences.unwrap().cliAlias?.shimPath);
    }

    const write = await this.#writeShim(alias);

    if (write.isErr()) {
      return Result.fail(write.unwrapError());
    }

    const profile = await this.#ensureShellProfilePath();

    if (profile.isErr()) {
      return Result.fail(profile.unwrapError());
    }

    const save = await this.#preferencesRepository.savePreferences({
      ...preferences.unwrap(),
      cliAlias: alias,
      updatedAt: now(),
    });

    return save.isOk() ? Result.ok(alias) : Result.fail(save.unwrapError());
  }

  shellCommand(): string {
    return this.activationCommand();
  }

  async syncAlias(): Promise<Result<AgentDevKitErrorCode, CliAliasState>> {
    const alias = await this.loadAlias();

    if (alias.isErr()) {
      return Result.fail(alias.unwrapError());
    }

    const current = alias.unwrap();

    if (current === undefined) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    return this.saveAlias(current.name, true);
  }

  async #hasUnsafeCollision(
    alias: CliAliasState,
    force: boolean,
  ): Promise<Result<AgentDevKitErrorCode, void>> {
    if (force) {
      return Result.ok(undefined);
    }

    for (const directory of this.#envPath.split(delimiter).filter(Boolean)) {
      const candidate = join(directory, alias.name);

      try {
        await access(candidate);
      } catch {
        continue;
      }

      if (candidate === alias.shimPath && (await this.#isManagedShim(candidate))) {
        return Result.ok(undefined);
      }

      return Result.fail(ErrorCodes.InvalidInput);
    }

    return Result.ok(undefined);
  }

  async #isManagedShim(path: string): Promise<boolean> {
    try {
      return (await readFile(path, "utf8")).includes("agent-devkit managed alias shim");
    } catch {
      return false;
    }
  }

  async #removeManagedShim(path: string | undefined): Promise<void> {
    if (path === undefined || !(await this.#isManagedShim(path))) {
      return;
    }

    await rm(path, { force: true });
  }

  #shimPath(name: string): string {
    return join(this.binDirectory(), name);
  }

  #shellProfilePath(): string {
    const shellName = basename(this.#shell);

    if (shellName === "zsh") {
      return join(this.#homeDirectory, ".zshrc");
    }

    if (shellName === "bash") {
      return join(this.#homeDirectory, ".bashrc");
    }

    return join(this.#homeDirectory, ".profile");
  }

  #validateName(name: string): Result<AgentDevKitErrorCode, string> {
    const parsed = CliAliasNameSchema.safeParse(name);

    if (!parsed.success || reservedAliases.has(parsed.data)) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    return Result.ok(parsed.data);
  }

  async #writeShim(alias: CliAliasState): Promise<Result<AgentDevKitErrorCode, void>> {
    const script = [
      "#!/usr/bin/env sh",
      "# agent-devkit managed alias shim",
      `exec ${this.#agentCommand} "$@"`,
      "",
    ].join("\n");

    try {
      await mkdir(dirname(alias.shimPath), { recursive: true, mode: 0o700 });
      await writeFile(alias.shimPath, script, "utf8");
      await chmod(alias.shimPath, 0o755);
      return Result.ok(undefined);
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }

  async #ensureShellProfilePath(): Promise<Result<AgentDevKitErrorCode, void>> {
    const profilePath = this.#shellProfilePath();
    const block = [
      "",
      "# agent-devkit managed PATH",
      `case ":$PATH:" in *":${this.binDirectory()}:"*) ;; *) export PATH="${this.binDirectory()}:$PATH" ;; esac`,
      "# /agent-devkit managed PATH",
      "",
    ].join("\n");

    try {
      await mkdir(dirname(profilePath), { recursive: true, mode: 0o700 });

      let current = "";

      try {
        current = await readFile(profilePath, "utf8");
      } catch {
        current = "";
      }

      if (!current.includes("# agent-devkit managed PATH")) {
        await writeFile(profilePath, `${current.trimEnd()}${block}`, {
          encoding: "utf8",
          mode: 0o600,
        });
      }

      return Result.ok(undefined);
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }
}
