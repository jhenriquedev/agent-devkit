export type StateResetRepository = {
  exists(path: string): Promise<boolean>;
  remove(path: string): Promise<void>;
};
