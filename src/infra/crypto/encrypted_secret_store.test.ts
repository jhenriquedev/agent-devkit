import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { EncryptedSecretStore } from "./encrypted_secret_store";
import { LocalSecretCrypto } from "./local_secret_crypto";

const key = Buffer.from("0123456789abcdef0123456789abcdef", "utf8");

describe("EncryptedSecretStore", () => {
  it("stores secrets encrypted and retrieves them by name", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-secrets-"));
    const store = new EncryptedSecretStore({
      crypto: new LocalSecretCrypto({ keyProvider: { getKey: async () => key } }),
      stateDirectory: join(root, ".agent-devkit"),
    });

    try {
      const saved = await store.set("openai.apiKey", "sk-test-secret", {
        service: "openai",
      });
      const listed = await store.list();
      const value = await store.get("openai.apiKey");
      const raw = await readFile(join(root, ".agent-devkit", "secrets", "vault.json"), "utf8");

      expect(saved.isOk()).toBe(true);
      expect(listed.unwrap()).toEqual([
        expect.objectContaining({
          name: "openai.apiKey",
          service: "openai",
        }),
      ]);
      expect(value.unwrap()).toBe("sk-test-secret");
      expect(raw).not.toContain("sk-test-secret");
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("removes a stored secret", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-secrets-"));
    const store = new EncryptedSecretStore({
      crypto: new LocalSecretCrypto({ keyProvider: { getKey: async () => key } }),
      stateDirectory: join(root, ".agent-devkit"),
    });

    try {
      await store.set("openai.apiKey", "sk-test-secret");
      const removed = await store.remove("openai.apiKey");
      const listed = await store.list();

      expect(removed.isOk()).toBe(true);
      expect(removed.unwrap()).toEqual({ removed: true });
      expect(listed.unwrap()).toEqual([]);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });
});
