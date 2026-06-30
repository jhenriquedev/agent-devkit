import { PlanSelfUpdate } from "../src/domain/usecases/PlanSelfUpdate";

describe("PlanSelfUpdate", () => {
  it("lists available versions with current and selected version", async () => {
    const result = await new PlanSelfUpdate({
      currentVersion: "0.4.0",
      packageName: "agent-devkit",
      packageManager: {
        installGlobal: async () => ({
          command: "npm install -g agent-devkit@0.4.2",
          executed: false,
        }),
      },
      registry: {
        getPackageVersions: async () => ({
          distTags: { latest: "0.4.2" },
          versions: ["0.3.2", "0.4.0", "0.4.1", "0.4.2"],
        }),
      },
    }).execute({ dryRun: true, latest: true, yes: false });

    expect(result).toMatchObject({
      status: "planned",
      currentVersion: "0.4.0",
      selectedVersion: "0.4.2",
      command: "npm install -g agent-devkit@0.4.2",
      executed: false,
    });
    expect(result.versions).toEqual([
      { version: "0.4.2", current: false, latest: true, selected: true },
      { version: "0.4.1", current: false, latest: false, selected: false },
      { version: "0.4.0", current: true, latest: false, selected: false },
      { version: "0.3.2", current: false, latest: false, selected: false },
    ]);
  });

  it("does not downgrade when npm latest is older than the current version", async () => {
    const result = await new PlanSelfUpdate({
      currentVersion: "0.4.0",
      packageName: "agent-devkit",
      packageManager: {
        installGlobal: async () => {
          throw new Error("install should not be planned");
        },
      },
      registry: {
        getPackageVersions: async () => ({
          distTags: { latest: "0.3.2" },
          versions: ["0.3.1", "0.3.2"],
        }),
      },
    }).execute({ dryRun: true, latest: true, yes: false });

    expect(result.status).toBe("current");
    expect(result.currentVersion).toBe("0.4.0");
    expect(result.selectedVersion).toBe("0.4.0");
    expect(result.command).toBe("");
    expect(result.versions[0]).toEqual({
      version: "0.4.0",
      current: true,
      latest: false,
      selected: true,
    });
  });
});
