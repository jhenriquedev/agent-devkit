import { homedir } from "node:os";
import type { ToolRuntime } from "../../infra/bases/tool_runtime";
import { createCapabilityToolRuntime } from "../../modules/capability_tool_runtime";

export type CliToolRuntimeOptions = {
  currentVersion: string;
  packageName: string;
};

export function createCliToolRuntime(options: CliToolRuntimeOptions): ToolRuntime {
  const homeDirectory = homedir();
  const runtime = createCapabilityToolRuntime({
    appVersion: options.currentVersion,
    context: { homeDirectory },
    currentVersion: options.currentVersion,
    logs: { homeDirectory },
    packageName: options.packageName,
    secrets: { homeDirectory },
    user: { homeDirectory },
  });

  if (runtime.isErr()) {
    throw new Error(runtime.unwrapError());
  }

  return runtime.unwrap();
}
