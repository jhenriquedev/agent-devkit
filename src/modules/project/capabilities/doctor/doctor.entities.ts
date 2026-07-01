import { z } from "zod";

export const DoctorInputSchema = z.object({}).strict();

export type DoctorStatus = "ok" | "warning" | "error";

export const DoctorReportSchema = z.object({
  status: z.enum(["ok", "warning", "error"]),
  version: z.string().min(1),
  node: z.object({
    version: z.string().min(1),
  }),
  system: z.object({
    platform: z.string().min(1),
    cwd: z.string().min(1),
  }),
  terminal: z.object({
    stdinIsTTY: z.boolean(),
    stdoutIsTTY: z.boolean(),
  }),
  runtime: z.object({
    globalState: z.object({
      path: z.string().min(1),
      exists: z.boolean(),
    }),
    projectState: z.object({
      path: z.string().min(1),
      exists: z.boolean(),
    }),
  }),
  models: z
    .object({
      directory: z.string().min(1),
      installed: z.number().int().nonnegative(),
      ids: z.array(z.string().min(1)),
    })
    .optional(),
});

export type DoctorStatePath = {
  path: string;
  exists: boolean;
};

export type DoctorReport = {
  status: DoctorStatus;
  version: string;
  node: {
    version: string;
  };
  system: {
    platform: string;
    cwd: string;
  };
  terminal: {
    stdinIsTTY: boolean;
    stdoutIsTTY: boolean;
  };
  runtime: {
    globalState: DoctorStatePath;
    projectState: DoctorStatePath;
  };
  models?: {
    directory: string;
    installed: number;
    ids: string[];
  };
};
