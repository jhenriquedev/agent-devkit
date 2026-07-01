import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";
import type { EncryptedPayload, SecretCrypto, SecretKeyProvider } from "../bases/crypto";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import type { Logger } from "../bases/logger";
import { NullLogger } from "../bases/logger";
import { Result } from "../bases/result";
import { errorCause } from "../helpers/error_cause";

export type LocalSecretCryptoOptions = {
  clock?: () => Date;
  keyProvider: SecretKeyProvider;
  logger?: Logger;
};

function keyId(provider: SecretKeyProvider): string {
  return provider.keyId?.() ?? "local";
}

async function resolveKey(provider: SecretKeyProvider): Promise<Buffer> {
  const key = await provider.getKey();
  return Buffer.isBuffer(key) ? key : Buffer.from(key);
}

export class LocalSecretCrypto implements SecretCrypto {
  readonly #clock: () => Date;
  readonly #keyProvider: SecretKeyProvider;
  readonly #logger: Logger;

  constructor(options: LocalSecretCryptoOptions) {
    this.#clock = options.clock ?? (() => new Date());
    this.#keyProvider = options.keyProvider;
    this.#logger = options.logger ?? new NullLogger();
  }

  async encryptString(value: string): Promise<Result<AgentDevKitErrorCode, EncryptedPayload>> {
    try {
      const key = await resolveKey(this.#keyProvider);

      if (key.length !== 32) {
        return Result.fail(ErrorCodes.EncryptionFailed);
      }

      const iv = randomBytes(12);
      const cipher = createCipheriv("aes-256-gcm", key, iv);
      const ciphertext = Buffer.concat([cipher.update(value, "utf8"), cipher.final()]);
      const authTag = cipher.getAuthTag();

      return Result.ok({
        algorithm: "aes-256-gcm",
        authTag: authTag.toString("base64"),
        ciphertext: ciphertext.toString("base64"),
        createdAt: this.#clock().toISOString(),
        iv: iv.toString("base64"),
        keyId: keyId(this.#keyProvider),
        schema: "agent-devkit.encrypted-payload/v1",
      });
    } catch (error) {
      this.#logger.write("error", "Secret encryption failed.", { error: errorCause(error) });
      return Result.fail(ErrorCodes.EncryptionFailed);
    }
  }

  async decryptString(payload: EncryptedPayload): Promise<Result<AgentDevKitErrorCode, string>> {
    try {
      const key = await resolveKey(this.#keyProvider);

      if (
        key.length !== 32 ||
        payload.algorithm !== "aes-256-gcm" ||
        payload.keyId !== keyId(this.#keyProvider)
      ) {
        return Result.fail(ErrorCodes.DecryptionFailed);
      }

      const decipher = createDecipheriv("aes-256-gcm", key, Buffer.from(payload.iv, "base64"));
      decipher.setAuthTag(Buffer.from(payload.authTag, "base64"));

      const decrypted = Buffer.concat([
        decipher.update(Buffer.from(payload.ciphertext, "base64")),
        decipher.final(),
      ]);

      return Result.ok(decrypted.toString("utf8"));
    } catch (error) {
      this.#logger.write("error", "Secret decryption failed.", { error: errorCause(error) });
      return Result.fail(ErrorCodes.DecryptionFailed);
    }
  }
}
