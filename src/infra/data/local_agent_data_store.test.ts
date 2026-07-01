import { mkdtemp, readdir, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { agentDataNamespacePolicy } from "../bases/data_store";
import { ErrorCodes } from "../bases/errors";
import { LocalAgentDataStore } from "./local_agent_data_store";

describe("LocalAgentDataStore", () => {
  it("resolves logical paths under the data root and blocks traversal", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-data-store-"));

    try {
      const store = new LocalAgentDataStore({ rootDirectory: join(root, ".agent-devkit", "data") });
      const resolved = store.resolve({
        namespace: "preferences",
        segments: ["preferences.json"],
      });
      const invalid = store.resolve({
        namespace: "preferences",
        segments: ["..", "secrets", "vault.json"],
      });

      expect(resolved.isOk()).toBe(true);
      expect(resolved.unwrap()).toBe(
        join(root, ".agent-devkit", "data", "preferences", "preferences.json"),
      );
      expect(invalid.isErr()).toBe(true);
      expect(invalid.unwrapError()).toBe(ErrorCodes.InvalidInput);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("writes and reads JSON without creating directories on missing reads", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-data-store-"));

    try {
      const store = new LocalAgentDataStore({ rootDirectory: join(root, ".agent-devkit", "data") });
      const path = { namespace: "preferences" as const, segments: ["preferences.json"] };
      const missing = await store.readJson(path);

      expect(missing.isErr()).toBe(true);
      await expect(readdir(join(root, ".agent-devkit"))).rejects.toThrow();

      const write = await store.writeJson(path, {
        schema: "example",
        theme: "default-purple",
      });
      const read = await store.readJson<{ theme: string }>(path);

      expect(write.isOk()).toBe(true);
      expect(read.isOk()).toBe(true);
      expect(read.unwrap().theme).toBe("default-purple");
      await expect(
        readFile(join(root, ".agent-devkit", "data", "preferences", "preferences.json"), "utf8"),
      ).resolves.toContain("default-purple");
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("appends and reads JSONL records", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-data-store-"));

    try {
      const store = new LocalAgentDataStore({ rootDirectory: join(root, ".agent-devkit", "data") });
      const path = { namespace: "logs" as const, segments: ["usage-2026-07-01.jsonl"] };

      await store.appendJsonl(path, { command: "doctor" });
      await store.appendJsonl(path, { command: "preferences" });

      const records = await store.readJsonl<{ command: string }>(path);

      expect(records.isOk()).toBe(true);
      expect(records.unwrap()).toEqual([{ command: "doctor" }, { command: "preferences" }]);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("lists and removes data entries", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-data-store-"));

    try {
      const store = new LocalAgentDataStore({ rootDirectory: join(root, ".agent-devkit", "data") });

      await store.writeText({ namespace: "logs", segments: ["b.txt"] }, "b");
      await store.writeText({ namespace: "logs", segments: ["a.txt"] }, "a");

      const entries = await store.list({ namespace: "logs", segments: [] });

      expect(entries.isOk()).toBe(true);
      expect(entries.unwrap().map((entry) => entry.name)).toEqual(["a.txt", "b.txt"]);

      const remove = await store.remove({ namespace: "logs", segments: ["a.txt"] });
      const exists = await store.exists({ namespace: "logs", segments: ["a.txt"] });

      expect(remove.isOk()).toBe(true);
      expect(exists.unwrap()).toBe(false);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("declares secrets as the only encrypted namespace by default", () => {
    expect(agentDataNamespacePolicy("secrets")).toEqual({ encrypted: true });
    expect(agentDataNamespacePolicy("logs")).toEqual({ encrypted: false });
  });
});
