import { z } from "zod";
import type {
  SecretAuditEntry,
  SecretSummary,
} from "../../../../infra/crypto/encrypted_secret_store";

const SecretViewSchema = z.object({
  createdAt: z.string().min(1),
  name: z.string().min(1),
  service: z.string().min(1).optional(),
  updatedAt: z.string().min(1),
  value: z.string().optional(),
});

const SecretAuditEntrySchema = z.object({
  action: z.enum(["created", "removed", "revealed", "rotated", "updated"]),
  name: z.string().min(1),
  service: z.string().min(1).optional(),
  timestamp: z.string().min(1),
});

export const SecretsVaultOptionsSchema = z.discriminatedUnion("action", [
  z
    .object({
      action: z.literal("audit"),
      name: z.string().min(1).optional(),
    })
    .strict(),
  z.object({ action: z.literal("list") }).strict(),
  z
    .object({
      action: z.literal("remove"),
      name: z.string().min(1),
    })
    .strict(),
  z
    .object({
      action: z.literal("rotate"),
      name: z.string().min(1),
      service: z.string().min(1).optional(),
      value: z.string().min(1),
    })
    .strict(),
  z
    .object({
      action: z.literal("set"),
      name: z.string().min(1),
      service: z.string().min(1).optional(),
      value: z.string().min(1),
    })
    .strict(),
  z
    .object({
      action: z.literal("show"),
      name: z.string().min(1),
      reveal: z.boolean().optional(),
    })
    .strict(),
]);

export type SecretView = SecretSummary & {
  value?: string;
};

export type SecretsVaultOptions =
  | { action: "audit"; name?: string }
  | { action: "list" }
  | { action: "remove"; name: string }
  | { action: "rotate"; name: string; service?: string; value: string }
  | { action: "set"; name: string; service?: string; value: string }
  | { action: "show"; name: string; reveal?: boolean };

export type SecretsVaultResult =
  | {
      action: "audit";
      events: SecretAuditEntry[];
      path: string;
    }
  | {
      action: "list";
      path: string;
      secrets: SecretView[];
    }
  | {
      action: "remove";
      path: string;
      removed: boolean;
      secret: { name: string };
    }
  | {
      action: "rotate";
      path: string;
      secret: SecretView;
    }
  | {
      action: "set";
      path: string;
      secret: SecretView;
    }
  | {
      action: "show";
      path: string;
      secret: SecretView;
    };

export const SecretsVaultResultSchema = z.discriminatedUnion("action", [
  z.object({
    action: z.literal("audit"),
    events: z.array(SecretAuditEntrySchema),
    path: z.string().min(1),
  }),
  z.object({
    action: z.literal("list"),
    path: z.string().min(1),
    secrets: z.array(SecretViewSchema),
  }),
  z.object({
    action: z.literal("remove"),
    path: z.string().min(1),
    removed: z.boolean(),
    secret: z.object({ name: z.string().min(1) }),
  }),
  z.object({
    action: z.literal("rotate"),
    path: z.string().min(1),
    secret: SecretViewSchema,
  }),
  z.object({
    action: z.literal("set"),
    path: z.string().min(1),
    secret: SecretViewSchema,
  }),
  z.object({
    action: z.literal("show"),
    path: z.string().min(1),
    secret: SecretViewSchema,
  }),
]);
