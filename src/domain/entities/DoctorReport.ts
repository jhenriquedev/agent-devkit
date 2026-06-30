export type DoctorStatus = "ok" | "warning" | "error";

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
};
