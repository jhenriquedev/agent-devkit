export type PackageVersions = {
  distTags: Record<string, string | undefined>;
  versions: string[];
};

export type PackageRegistry = {
  getPackageVersions(packageName: string): Promise<PackageVersions>;
};
