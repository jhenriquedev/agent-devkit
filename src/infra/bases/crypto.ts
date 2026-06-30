import type { AgentDevKitErrorCode } from "./errors";
import type { Result } from "./result";

export type EncryptedPayload = {
  algorithm: "aes-256-gcm";
  authTag: string;
  ciphertext: string;
  createdAt: string;
  iv: string;
  keyId: string;
  schema: "agent-devkit.encrypted-payload/v1";
};

export interface SecretKeyProvider {
  getKey(): Promise<Buffer> | Buffer;
  keyId?(): string;
}

export interface SecretCrypto {
  decryptString(payload: EncryptedPayload): Promise<Result<AgentDevKitErrorCode, string>>;
  encryptString(value: string): Promise<Result<AgentDevKitErrorCode, EncryptedPayload>>;
}
