import { z } from "zod";

export const DependencyActionSchema = z.enum([
  "check",
  "check-compatibility",
  "check-environment",
  "check-installed",
  "configure",
  "downgrade",
  "install",
  "list",
  "plan-configure",
  "plan-downgrade",
  "plan-install",
  "plan-uninstall",
  "plan-upgrade",
  "uninstall",
  "upgrade",
  "verify",
]);

export const DependencyStatusSchema = z.enum([
  "compatible",
  "configured",
  "incompatible",
  "installed",
  "missing",
  "ok",
  "planned",
  "unsupported",
  "warning",
]);

export const DependencyRiskSchema = z.enum(["read-only", "writes-external", "writes-global-state"]);

export const DependenciesOptionsSchema = z
  .object({
    action: DependencyActionSchema,
    confirmed: z.boolean().optional(),
    dependency: z.string().min(1).optional(),
    options: z.record(z.string(), z.unknown()).optional(),
    version: z.string().min(1).optional(),
  })
  .strict();

export type DependenciesOptions = z.infer<typeof DependenciesOptionsSchema>;

export const DependencyMetadataSchema = z.object({
  category: z.string().min(1),
  description: z.string().min(1),
  id: z.string().min(1),
  name: z.string().min(1),
  risk: DependencyRiskSchema,
});

export type DependencyMetadataView = z.infer<typeof DependencyMetadataSchema>;

export const DependencyCheckSchema = z.object({
  details: z.record(z.string(), z.unknown()).optional(),
  id: z.string().min(1),
  message: z.string().min(1),
  status: DependencyStatusSchema,
});

export const DependencyCommandPlanSchema = z.object({
  command: z.string().min(1),
  description: z.string().min(1),
  risk: DependencyRiskSchema,
});

export const DependencyPlanSchema = z.object({
  commands: z.array(DependencyCommandPlanSchema),
  id: z.string().min(1),
  message: z.string().min(1),
  requiresApproval: z.boolean(),
  status: DependencyStatusSchema,
});

export const DependencyOperationResultSchema = z.object({
  id: z.string().min(1),
  message: z.string().min(1),
  status: DependencyStatusSchema,
});

export const DependenciesResultSchema = z.discriminatedUnion("action", [
  z.object({
    action: z.literal("list"),
    dependencies: z.array(DependencyMetadataSchema),
    status: DependencyStatusSchema,
  }),
  z.object({
    action: z.enum([
      "check",
      "check-compatibility",
      "check-environment",
      "check-installed",
      "verify",
    ]),
    checks: z.array(DependencyCheckSchema),
    dependency: z.string().min(1).optional(),
    status: DependencyStatusSchema,
  }),
  z.object({
    action: z.enum([
      "plan-configure",
      "plan-downgrade",
      "plan-install",
      "plan-uninstall",
      "plan-upgrade",
    ]),
    dependency: z.string().min(1),
    plan: DependencyPlanSchema,
    status: DependencyStatusSchema,
  }),
  z.object({
    action: z.enum(["configure", "downgrade", "install", "uninstall", "upgrade"]),
    dependency: z.string().min(1),
    result: DependencyOperationResultSchema,
    status: DependencyStatusSchema,
  }),
]);

export type DependenciesResult = z.infer<typeof DependenciesResultSchema>;
