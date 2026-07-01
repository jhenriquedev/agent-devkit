import { LocalSecretCrypto } from "./local_secret_crypto";

const key = Buffer.from("0123456789abcdef0123456789abcdef", "utf8");

describe("LocalSecretCrypto", () => {
  it("encrypts and decrypts strings without storing plaintext", async () => {
    const crypto = new LocalSecretCrypto({ keyProvider: { getKey: async () => key } });

    const encrypted = await crypto.encryptString("sk-test-secret");

    expect(encrypted.isOk()).toBe(true);
    expect(JSON.stringify(encrypted.unwrap())).not.toContain("sk-test-secret");

    const decrypted = await crypto.decryptString(encrypted.unwrap());

    expect(decrypted.isOk()).toBe(true);
    expect(decrypted.unwrap()).toBe("sk-test-secret");
  });

  it("fails to decrypt tampered payloads", async () => {
    const crypto = new LocalSecretCrypto({ keyProvider: { getKey: async () => key } });
    const encrypted = await crypto.encryptString("sk-test-secret");

    const decrypted = await crypto.decryptString({
      ...encrypted.unwrap(),
      ciphertext: encrypted.unwrap().ciphertext.replace(/.$/, "A"),
    });

    expect(decrypted.isErr()).toBe(true);
  });

  it("fails to decrypt payloads encrypted with another key id", async () => {
    const crypto = new LocalSecretCrypto({
      keyProvider: { getKey: async () => key, keyId: () => "local-a" },
    });
    const encrypted = await crypto.encryptString("sk-test-secret");
    const rotatedKeyCrypto = new LocalSecretCrypto({
      keyProvider: { getKey: async () => key, keyId: () => "local-b" },
    });

    const decrypted = await rotatedKeyCrypto.decryptString(encrypted.unwrap());

    expect(decrypted.isErr()).toBe(true);
  });
});
