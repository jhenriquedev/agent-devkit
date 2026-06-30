export type ProjectInitStatus = "already-initialized" | "initialized" | "planned";

export type ProjectInitFile = {
  content: unknown;
  path: string;
};

export type ProjectInitResult = {
  status: ProjectInitStatus;
  version: string;
  project: {
    root: string;
  };
  planned: string[];
  created: string[];
  skipped: string[];
};
