import { z } from "zod";

export const UpdateServiceOptionsSchema = z
  .object({
    dryRun: z.boolean(),
    latest: z.boolean(),
    version: z.string().min(1).optional(),
    yes: z.boolean(),
  })
  .strict();

export type SelfUpdateStatus = "current" | "planned" | "updated";

export type PackageVersionOption = {
  version: string;
  current: boolean;
  latest: boolean;
  selected: boolean;
};

export type SelfUpdateResult = {
  status: SelfUpdateStatus;
  packageName: string;
  currentVersion: string;
  selectedVersion: string;
  command: string;
  executed: boolean;
  versions: PackageVersionOption[];
};

export const SelfUpdateResultSchema = z.object({
  status: z.enum(["current", "planned", "updated"]),
  packageName: z.string().min(1),
  currentVersion: z.string().min(1),
  selectedVersion: z.string().min(1),
  command: z.string(),
  executed: z.boolean(),
  versions: z.array(
    z.object({
      version: z.string().min(1),
      current: z.boolean(),
      latest: z.boolean(),
      selected: z.boolean(),
    }),
  ),
});

export type UpdateServiceOptions = z.infer<typeof UpdateServiceOptionsSchema>;

export type PackageVersions = {
  distTags: Record<string, string | undefined>;
  versions: string[];
};

export type PackageInstallResult = {
  command: string;
  executed: boolean;
};
