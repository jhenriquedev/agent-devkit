export const ErrorCodes = {
  CapabilityExecutionFailed: "CAPABILITY_EXECUTION_FAILED",
  FileReadFailed: "FILE_READ_FAILED",
  FileWriteFailed: "FILE_WRITE_FAILED",
  InvalidInput: "INVALID_INPUT",
  NetworkRequestFailed: "NETWORK_REQUEST_FAILED",
  PackageInstallFailed: "PACKAGE_INSTALL_FAILED",
  PackageRegistryFailed: "PACKAGE_REGISTRY_FAILED",
  StateResetFailed: "STATE_RESET_FAILED",
} as const;

export type AgentDevKitErrorCode = (typeof ErrorCodes)[keyof typeof ErrorCodes];
