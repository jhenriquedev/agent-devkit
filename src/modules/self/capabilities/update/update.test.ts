import { Result } from "../../../../infra/bases/result";
import { UpdateService } from "./update.service";

describe("self.update", () => {
  it("lists available versions with current and selected version", async () => {
    const result = await new UpdateService({
      currentVersion: "0.3.4",
      packageName: "agent-devkit",
      repository: {
        repositoryId: "test.update.repository",
        installGlobal: async () =>
          Result.ok({
            command: "npm install -g agent-devkit@0.4.2",
            executed: false,
          }),
        getPackageVersions: async () =>
          Result.ok({
            distTags: { latest: "0.4.2" },
            versions: ["0.3.2", "0.3.4", "0.4.1", "0.4.2"],
          }),
      },
    }).execute({ dryRun: true, latest: true, yes: false });

    expect(result.isOk()).toBe(true);
    const payload = result.unwrap();
    expect(payload).toMatchObject({
      status: "planned",
      currentVersion: "0.3.4",
      selectedVersion: "0.4.2",
      command: "npm install -g agent-devkit@0.4.2",
      executed: false,
    });
    expect(payload.versions).toEqual([
      { version: "0.4.2", current: false, latest: true, selected: true },
      { version: "0.4.1", current: false, latest: false, selected: false },
      { version: "0.3.4", current: true, latest: false, selected: false },
      { version: "0.3.2", current: false, latest: false, selected: false },
    ]);
  });

  it("does not downgrade when npm latest is older than the current version", async () => {
    const result = await new UpdateService({
      currentVersion: "0.3.4",
      packageName: "agent-devkit",
      repository: {
        repositoryId: "test.update.repository",
        installGlobal: async () => {
          throw new Error("install should not be planned");
        },
        getPackageVersions: async () =>
          Result.ok({
            distTags: { latest: "0.3.2" },
            versions: ["0.3.1", "0.3.2"],
          }),
      },
    }).execute({ dryRun: true, latest: true, yes: false });

    expect(result.isOk()).toBe(true);
    const payload = result.unwrap();
    expect(payload.status).toBe("current");
    expect(payload.currentVersion).toBe("0.3.4");
    expect(payload.selectedVersion).toBe("0.3.4");
    expect(payload.command).toBe("");
    expect(payload.versions[0]).toEqual({
      version: "0.3.4",
      current: true,
      latest: false,
      selected: true,
    });
  });

  it("keeps the current version selected unless latest or an explicit version is requested", async () => {
    const result = await new UpdateService({
      currentVersion: "0.3.4",
      packageName: "agent-devkit",
      repository: {
        repositoryId: "test.update.repository",
        installGlobal: async () => {
          throw new Error("install should not be planned");
        },
        getPackageVersions: async () =>
          Result.ok({
            distTags: { latest: "0.4.2" },
            versions: ["0.3.4", "0.4.1", "0.4.2"],
          }),
      },
    }).execute({ dryRun: true, latest: false, yes: false });

    expect(result.isOk()).toBe(true);
    expect(result.unwrap()).toMatchObject({
      status: "current",
      selectedVersion: "0.3.4",
      command: "",
      executed: false,
    });
    expect(result.unwrap().versions).toEqual([
      { version: "0.4.2", current: false, latest: true, selected: false },
      { version: "0.4.1", current: false, latest: false, selected: false },
      { version: "0.3.4", current: true, latest: false, selected: true },
    ]);
  });
});
