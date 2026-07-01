import { access, mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { PreferencesRepository } from "../preferences/preferences.repository";
import { CliAliasRepository } from "./cliAlias.repository";
import { CliAliasService } from "./cliAlias.service";

function service(root: string, envPath?: string, shell = "/bin/sh"): CliAliasService {
  return new CliAliasService({
    repository: new CliAliasRepository({
      envPath,
      homeDirectory: root,
      preferencesRepository: new PreferencesRepository({ homeDirectory: root }),
      shell,
    }),
  });
}

describe("user.cliAlias", () => {
  it("creates a managed shim and stores alias preferences", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-cli-alias-"));
    const alias = service(root, join(root, ".agent-devkit", "bin"));

    try {
      const result = await alias.execute({ action: "set", name: "kit" });
      const shim = await readFile(join(root, ".agent-devkit", "bin", "kit"), "utf8");
      const shellProfile = await readFile(join(root, ".profile"), "utf8");
      const preferences = await readFile(
        join(root, ".agent-devkit", "data", "preferences", "preferences.json"),
        "utf8",
      );

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        alias: {
          enabled: true,
          name: "kit",
        },
        binDirectoryInPath: true,
        status: "configured",
      });
      expect(shim).toContain("agent");
      expect(shellProfile).toContain("# agent-devkit managed PATH");
      expect(shellProfile).toContain(join(root, ".agent-devkit", "bin"));
      expect(preferences).toContain('"cliAlias"');
      expect(preferences).toContain('"kit"');
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("removes the managed shim without removing the agent command", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-cli-alias-"));
    const alias = service(root);

    try {
      await alias.execute({ action: "set", name: "kit" });
      const removed = await alias.execute({ action: "remove" });

      expect(removed.isOk()).toBe(true);
      expect(removed.unwrap()).toMatchObject({
        alias: undefined,
        status: "removed",
      });
      await expect(access(join(root, ".agent-devkit", "bin", "kit"))).rejects.toThrow();
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("prints an activation command for the current shell", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-cli-alias-"));
    const alias = service(root, "");

    try {
      const result = await alias.execute({ action: "shell" });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        binDirectoryInPath: false,
        shellCommand: expect.stringContaining(".agent-devkit/bin"),
        status: "shell",
      });
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("rejects invalid or reserved alias names", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-cli-alias-"));
    const alias = service(root);

    try {
      const agent = await alias.execute({ action: "set", name: "agent" });
      const spaced = await alias.execute({ action: "set", name: "kit dev" } as never);

      expect(agent.isErr()).toBe(true);
      expect(spaced.isErr()).toBe(true);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });
});
