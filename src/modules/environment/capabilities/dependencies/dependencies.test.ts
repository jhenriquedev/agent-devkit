import { ErrorCodes } from "../../../../infra/bases/errors";
import { DependenciesRepository } from "./dependencies.repository";
import { DependenciesService } from "./dependencies.service";
import { NodeDependencyProvider } from "./providers/node.provider";

function service() {
  return new DependenciesService({
    repository: new DependenciesRepository({
      providers: [new NodeDependencyProvider()],
    }),
  });
}

describe("environment.dependencies", () => {
  it("lists known dependency providers", async () => {
    const result = await service().execute({ action: "list" });

    expect(result.isOk()).toBe(true);
    expect(result.unwrap()).toMatchObject({
      action: "list",
      dependencies: [
        {
          id: "node",
          name: "Node.js",
          risk: "read-only",
        },
      ],
      status: "ok",
    });
  });

  it("verifies the current Node.js runtime", async () => {
    const result = await service().execute({ action: "verify", dependency: "node" });

    expect(result.isOk()).toBe(true);
    expect(result.unwrap()).toMatchObject({
      action: "verify",
      checks: [
        {
          id: "node",
          status: "ok",
        },
      ],
      dependency: "node",
      status: "ok",
    });
  });

  it("rejects unknown dependencies", async () => {
    const result = await service().execute({ action: "verify", dependency: "aws-cli" });

    expect(result.isErr()).toBe(true);
    expect(result.unwrapError()).toBe(ErrorCodes.InvalidInput);
  });

  it("plans unsupported install operations without side effects", async () => {
    const result = await service().execute({ action: "plan-install", dependency: "node" });

    expect(result.isOk()).toBe(true);
    expect(result.unwrap()).toMatchObject({
      action: "plan-install",
      dependency: "node",
      plan: {
        commands: [],
        requiresApproval: false,
        status: "unsupported",
      },
      status: "unsupported",
    });
  });

  it("returns a plan when mutating actions are not confirmed", async () => {
    const result = await service().execute({ action: "install", dependency: "node" });

    expect(result.isOk()).toBe(true);
    expect(result.unwrap()).toMatchObject({
      action: "plan-install",
      dependency: "node",
      status: "unsupported",
    });
  });

  it("returns unsupported for confirmed Node.js install", async () => {
    const result = await service().execute({
      action: "install",
      confirmed: true,
      dependency: "node",
    });

    expect(result.isOk()).toBe(true);
    expect(result.unwrap()).toMatchObject({
      action: "install",
      dependency: "node",
      result: {
        status: "unsupported",
      },
      status: "unsupported",
    });
  });
});
