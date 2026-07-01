import type {
  DependencyCheck,
  DependencyMetadata,
  DependencyOperationResult,
  DependencyPlan,
  DependencyProvider,
} from "../../../../../infra/bases/dependency";
import type { AgentDevKitErrorCode } from "../../../../../infra/bases/errors";
import { Result } from "../../../../../infra/bases/result";

const minimumMajorVersion = 20;

function nodeMajorVersion(): number {
  return Number.parseInt(process.versions.node.split(".")[0] ?? "0", 10);
}

function unsupportedPlan(id: string, action: string): DependencyPlan {
  return {
    commands: [],
    id,
    message: `${action} is not supported for Node.js by Agent DevKit yet.`,
    requiresApproval: false,
    status: "unsupported",
  };
}

function unsupportedResult(id: string, action: string): DependencyOperationResult {
  return {
    id,
    message: `${action} is not supported for Node.js by Agent DevKit yet.`,
    status: "unsupported",
  };
}

export class NodeDependencyProvider implements DependencyProvider {
  readonly #id = "node";

  metadata(): DependencyMetadata {
    return {
      category: "runtime",
      description: "Node.js runtime used by Agent DevKit.",
      id: this.#id,
      name: "Node.js",
      risk: "read-only",
    };
  }

  async checkEnvironment(): Promise<Result<AgentDevKitErrorCode, DependencyCheck>> {
    return Result.ok({
      details: {
        arch: process.arch,
        platform: process.platform,
      },
      id: this.#id,
      message: `Running on ${process.platform}/${process.arch}.`,
      status: "ok",
    });
  }

  async checkInstalled(): Promise<Result<AgentDevKitErrorCode, DependencyCheck>> {
    return Result.ok({
      details: {
        execPath: process.execPath,
        version: process.version,
      },
      id: this.#id,
      message: `Node.js ${process.version} is available.`,
      status: "installed",
    });
  }

  async checkCompatibility(): Promise<Result<AgentDevKitErrorCode, DependencyCheck>> {
    const compatible = nodeMajorVersion() >= minimumMajorVersion;

    return Result.ok({
      details: {
        current: process.version,
        required: `>=${minimumMajorVersion}`,
      },
      id: this.#id,
      message: compatible
        ? `Node.js ${process.version} is compatible.`
        : `Node.js ${process.version} is below the required major version ${minimumMajorVersion}.`,
      status: compatible ? "compatible" : "incompatible",
    });
  }

  async verify(): Promise<Result<AgentDevKitErrorCode, DependencyCheck>> {
    const compatibility = await this.checkCompatibility();

    if (compatibility.isErr()) {
      return compatibility;
    }

    const compatible = compatibility.unwrap();

    return Result.ok({
      details: {
        execPath: process.execPath,
        platform: process.platform,
        required: `>=${minimumMajorVersion}`,
        version: process.version,
      },
      id: this.#id,
      message:
        compatible.status === "compatible" ? "Node.js runtime is ready." : compatible.message,
      status: compatible.status === "compatible" ? "ok" : "incompatible",
    });
  }

  async planInstall(): Promise<Result<AgentDevKitErrorCode, DependencyPlan>> {
    return Result.ok(unsupportedPlan(this.#id, "Install"));
  }

  async install(): Promise<Result<AgentDevKitErrorCode, DependencyOperationResult>> {
    return Result.ok(unsupportedResult(this.#id, "Install"));
  }

  async planConfigure(): Promise<Result<AgentDevKitErrorCode, DependencyPlan>> {
    return Result.ok({
      commands: [],
      id: this.#id,
      message: "Node.js does not require Agent DevKit credential configuration.",
      requiresApproval: false,
      status: "planned",
    });
  }

  async configure(): Promise<Result<AgentDevKitErrorCode, DependencyOperationResult>> {
    return Result.ok({
      id: this.#id,
      message: "Node.js does not require Agent DevKit credential configuration.",
      status: "configured",
    });
  }

  async planUpgrade(): Promise<Result<AgentDevKitErrorCode, DependencyPlan>> {
    return Result.ok(unsupportedPlan(this.#id, "Upgrade"));
  }

  async upgrade(): Promise<Result<AgentDevKitErrorCode, DependencyOperationResult>> {
    return Result.ok(unsupportedResult(this.#id, "Upgrade"));
  }

  async planDowngrade(): Promise<Result<AgentDevKitErrorCode, DependencyPlan>> {
    return Result.ok(unsupportedPlan(this.#id, "Downgrade"));
  }

  async downgrade(): Promise<Result<AgentDevKitErrorCode, DependencyOperationResult>> {
    return Result.ok(unsupportedResult(this.#id, "Downgrade"));
  }

  async planUninstall(): Promise<Result<AgentDevKitErrorCode, DependencyPlan>> {
    return Result.ok(unsupportedPlan(this.#id, "Uninstall"));
  }

  async uninstall(): Promise<Result<AgentDevKitErrorCode, DependencyOperationResult>> {
    return Result.ok(unsupportedResult(this.#id, "Uninstall"));
  }
}
