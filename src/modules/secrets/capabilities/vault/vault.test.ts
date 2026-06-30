import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { EncryptedSecretStore } from "../../../../infra/crypto/encrypted_secret_store";
import { LocalSecretCrypto } from "../../../../infra/crypto/local_secret_crypto";
import { SecretsVaultRepository } from "./vault.repository";
import { SecretsVaultService } from "./vault.service";

const key = Buffer.from("0123456789abcdef0123456789abcdef", "utf8");

function service(root: string): SecretsVaultService {
  return new SecretsVaultService({
    repository: new SecretsVaultRepository({
      store: new EncryptedSecretStore({
        crypto: new LocalSecretCrypto({ keyProvider: { getKey: async () => key } }),
        stateDirectory: join(root, ".agent-devkit"),
      }),
    }),
  });
}

describe("secrets.vault", () => {
  it("sets, lists, reveals and removes encrypted secrets", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-secrets-module-"));
    const vault = service(root);

    try {
      const saved = await vault.execute({
        action: "set",
        name: "openai.apiKey",
        service: "openai",
        value: "sk-test-secret",
      });
      const listed = await vault.execute({ action: "list" });
      const masked = await vault.execute({ action: "show", name: "openai.apiKey" });
      const revealed = await vault.execute({ action: "show", name: "openai.apiKey", reveal: true });
      const removed = await vault.execute({ action: "remove", name: "openai.apiKey" });

      expect(saved.isOk()).toBe(true);
      expect(saved.unwrap()).toMatchObject({ action: "set", secret: { name: "openai.apiKey" } });
      expect(JSON.stringify(saved.unwrap())).not.toContain("sk-test-secret");
      expect(listed.unwrap()).toMatchObject({
        action: "list",
        secrets: [{ name: "openai.apiKey", service: "openai" }],
      });
      expect(masked.unwrap()).toMatchObject({
        action: "show",
        secret: { name: "openai.apiKey", value: "********" },
      });
      expect(revealed.unwrap()).toMatchObject({
        action: "show",
        secret: { name: "openai.apiKey", value: "sk-test-secret" },
      });
      expect(removed.unwrap()).toMatchObject({ action: "remove", removed: true });
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("rotates credentials and exposes a timestamped audit trail", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-secrets-module-"));
    const vault = service(root);

    try {
      const saved = await vault.execute({
        action: "set",
        name: "openai.apiKey",
        service: "openai",
        value: "sk-test-secret",
      });
      const rotated = await vault.execute({
        action: "rotate",
        name: "openai.apiKey",
        value: "sk-rotated-secret",
      });
      const audit = await vault.execute({ action: "audit", name: "openai.apiKey" });
      const revealed = await vault.execute({ action: "show", name: "openai.apiKey", reveal: true });

      expect(saved.isOk()).toBe(true);
      expect(rotated.unwrap()).toMatchObject({
        action: "rotate",
        secret: { name: "openai.apiKey", service: "openai", value: "********" },
      });
      expect(audit.unwrap()).toMatchObject({
        action: "audit",
        events: [
          expect.objectContaining({ action: "created", name: "openai.apiKey" }),
          expect.objectContaining({ action: "rotated", name: "openai.apiKey" }),
        ],
      });
      expect(revealed.unwrap()).toMatchObject({
        action: "show",
        secret: { name: "openai.apiKey", value: "sk-rotated-secret" },
      });
      expect(JSON.stringify(audit.unwrap())).not.toContain("sk-test-secret");
      expect(JSON.stringify(audit.unwrap())).not.toContain("sk-rotated-secret");
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });
});
