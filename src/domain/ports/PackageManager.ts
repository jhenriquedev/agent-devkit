export type PackageInstallResult = {
  command: string;
  executed: boolean;
};

export type PackageManager = {
  installGlobal(
    packageName: string,
    version: string,
    options: { dryRun: boolean },
  ): Promise<PackageInstallResult>;
};
