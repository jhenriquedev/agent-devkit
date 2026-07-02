export const ErrorCodes = {
  AssetReadFailed: "ASSET_READ_FAILED",
  ApprovalRequired: "APPROVAL_REQUIRED",
  BrainProviderUnavailable: "BRAIN_PROVIDER_UNAVAILABLE",
  CacheReadFailed: "CACHE_READ_FAILED",
  CapabilityNotFound: "CAPABILITY_NOT_FOUND",
  CapabilityExecutionFailed: "CAPABILITY_EXECUTION_FAILED",
  DatabaseReadFailed: "DATABASE_READ_FAILED",
  DecryptionFailed: "DECRYPTION_FAILED",
  EncryptionFailed: "ENCRYPTION_FAILED",
  FileReadFailed: "FILE_READ_FAILED",
  FileWriteFailed: "FILE_WRITE_FAILED",
  InvalidInput: "INVALID_INPUT",
  ModelNotFound: "MODEL_NOT_FOUND",
  ModelVerificationFailed: "MODEL_VERIFICATION_FAILED",
  NetworkRequestFailed: "NETWORK_REQUEST_FAILED",
  PackageInstallFailed: "PACKAGE_INSTALL_FAILED",
  PackageRegistryFailed: "PACKAGE_REGISTRY_FAILED",
  StateResetFailed: "STATE_RESET_FAILED",
} as const;

export type AgentDevKitErrorCode = (typeof ErrorCodes)[keyof typeof ErrorCodes];
