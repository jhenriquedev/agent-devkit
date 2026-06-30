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

export type PackageVersions = {
  distTags: Record<string, string | undefined>;
  versions: string[];
};

export type PackageInstallResult = {
  command: string;
  executed: boolean;
};
