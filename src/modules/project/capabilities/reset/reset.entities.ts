export type ResetScope = "global" | "project";
export type ResetStatus = "missing" | "planned" | "reset";

export type ResetResult = {
  scope: ResetScope;
  status: ResetStatus;
  path: string;
  removed: boolean;
};
