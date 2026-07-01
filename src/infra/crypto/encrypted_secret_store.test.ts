import { chmod, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { EncryptedSecretStore } from "./encrypted_secret_store";
import { LocalMasterKeyProvider } from "./local_master_key_provider";
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
      const raw = await readFile(
        join(root, ".agent-devkit", "data", "secrets", "vault.json"),
        "utf8",
      );

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

  it("audits secret lifecycle changes without storing plaintext", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-secrets-"));
    let now = new Date("2026-06-30T12:00:00.000Z");
    const store = new EncryptedSecretStore({
      clock: () => now,
      crypto: new LocalSecretCrypto({ keyProvider: { getKey: async () => key } }),
      stateDirectory: join(root, ".agent-devkit"),
    });

    try {
      await store.set("openai.apiKey", "sk-created", { service: "openai" });
      now = new Date("2026-06-30T12:05:00.000Z");
      await store.set("openai.apiKey", "sk-updated", { service: "openai" });
      now = new Date("2026-06-30T12:10:00.000Z");
      await store.rotate("openai.apiKey", "sk-rotated");
      now = new Date("2026-06-30T12:15:00.000Z");
      await store.reveal("openai.apiKey");
      now = new Date("2026-06-30T12:20:00.000Z");
      await store.remove("openai.apiKey");

      const audit = await store.audit("openai.apiKey");
      const raw = await readFile(
        join(root, ".agent-devkit", "data", "secrets", "vault.json"),
        "utf8",
      );

      expect(audit.unwrap()).toEqual([
        {
          action: "created",
          name: "openai.apiKey",
          service: "openai",
          timestamp: "2026-06-30T12:00:00.000Z",
        },
        {
          action: "updated",
          name: "openai.apiKey",
          service: "openai",
          timestamp: "2026-06-30T12:05:00.000Z",
        },
        {
          action: "rotated",
          name: "openai.apiKey",
          service: "openai",
          timestamp: "2026-06-30T12:10:00.000Z",
        },
        {
          action: "revealed",
          name: "openai.apiKey",
          service: "openai",
          timestamp: "2026-06-30T12:15:00.000Z",
        },
        {
          action: "removed",
          name: "openai.apiKey",
          service: "openai",
          timestamp: "2026-06-30T12:20:00.000Z",
        },
      ]);
      expect(raw).not.toContain("sk-created");
      expect(raw).not.toContain("sk-updated");
      expect(raw).not.toContain("sk-rotated");
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

  it("migrates a legacy vault into the canonical data directory", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-secrets-"));
    const crypto = new LocalSecretCrypto({ keyProvider: { getKey: async () => key } });
    const encrypted = await crypto.encryptString("sk-legacy-secret");
    const stateDirectory = join(root, ".agent-devkit");
    const legacyDirectory = join(stateDirectory, "secrets");
    const legacyPath = join(legacyDirectory, "vault.json");
    const canonicalPath = join(stateDirectory, "data", "secrets", "vault.json");
    const store = new EncryptedSecretStore({
      crypto,
      stateDirectory,
    });

    try {
      await mkdir(legacyDirectory, { recursive: true });
      await writeFile(
        legacyPath,
        `${JSON.stringify({
          audit: [],
          schema: "agent-devkit.secret-vault/v1",
          secrets: [
            {
              createdAt: "2026-06-30T12:00:00.000Z",
              encrypted: encrypted.unwrap(),
              name: "openai.apiKey",
              service: "openai",
              updatedAt: "2026-06-30T12:00:00.000Z",
            },
          ],
        })}\n`,
      );

      const value = await store.get("openai.apiKey");

      expect(value.unwrap()).toBe("sk-legacy-secret");
      await expect(readFile(canonicalPath, "utf8")).resolves.toContain("openai.apiKey");
      await expect(readFile(legacyPath, "utf8")).resolves.toContain("openai.apiKey");
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("does not treat inaccessible canonical vault directories as empty vaults", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-secrets-"));
    const stateDirectory = join(root, ".agent-devkit");
    const canonicalDirectory = join(stateDirectory, "data", "secrets");
    const store = new EncryptedSecretStore({
      crypto: new LocalSecretCrypto({ keyProvider: { getKey: async () => key } }),
      stateDirectory,
    });

    try {
      await mkdir(canonicalDirectory, { recursive: true });
      await chmod(canonicalDirectory, 0o000);

      const listed = await store.list();

      expect(listed.isErr()).toBe(true);
      expect(listed.unwrapError()).toBe("FILE_READ_FAILED");
    } finally {
      await chmod(canonicalDirectory, 0o700).catch(() => undefined);
      await rm(root, { force: true, recursive: true });
    }
  });
});

describe("LocalMasterKeyProvider", () => {
  it("creates the local master key under keys/master.key", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-master-key-"));
    const provider = new LocalMasterKeyProvider({ stateDirectory: join(root, ".agent-devkit") });

    try {
      const key = await provider.getKey();
      const persisted = await readFile(join(root, ".agent-devkit", "keys", "master.key"), "utf8");

      expect(key).toHaveLength(32);
      expect(Buffer.from(persisted.trim(), "base64")).toHaveLength(32);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("migrates a legacy local key into keys/master.key", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-master-key-"));
    const stateDirectory = join(root, ".agent-devkit");
    const legacyKey = Buffer.from("fedcba9876543210fedcba9876543210", "utf8");
    await mkdir(join(stateDirectory, "keys"), { recursive: true });
    await writeFile(join(stateDirectory, "keys", "local.key"), `${legacyKey.toString("base64")}\n`);
    const provider = new LocalMasterKeyProvider({ stateDirectory });

    try {
      const key = await provider.getKey();
      const persisted = await readFile(join(stateDirectory, "keys", "master.key"), "utf8");

      expect(key).toEqual(legacyKey);
      expect(Buffer.from(persisted.trim(), "base64")).toEqual(legacyKey);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });
});
