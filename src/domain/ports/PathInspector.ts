export type PathInspector = {
  exists(path: string): Promise<boolean>;
};
