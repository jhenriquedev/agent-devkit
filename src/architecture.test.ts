import { access, readdir } from "node:fs/promises";
import { join } from "node:path";
import { createProjectModuleBindings } from "./modules/project/project.bind";
import { projectModuleConfig } from "./modules/project/project.config";
import { createSelfModuleBindings } from "./modules/self/self.bind";
import { selfModuleConfig } from "./modules/self/self.config";

async function exists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

describe("canonical architecture", () => {
  it("does not keep a root tests directory", async () => {
    await expect(readdir(join(process.cwd(), "tests"))).rejects.toThrow();
  });

  it("keeps shared assets in canonical folders", async () => {
    await expect(exists(join(process.cwd(), "src", "assets", "i18n", ".gitkeep"))).resolves.toBe(
      true,
    );
    await expect(exists(join(process.cwd(), "src", "assets", "images", ".gitkeep"))).resolves.toBe(
      true,
    );
    await expect(exists(join(process.cwd(), "src", "assets", "fonts", ".gitkeep"))).resolves.toBe(
      true,
    );
    await expect(exists(join(process.cwd(), "src", "assets", "themes", ".gitkeep"))).resolves.toBe(
      true,
    );
  });

  it("keeps global infra bases available", async () => {
    for (const baseFile of [
      "assets.ts",
      "bind.ts",
      "capability.ts",
      "config.ts",
      "database.ts",
      "errors.ts",
      "logger.ts",
      "module.ts",
      "result.ts",
      "serializer.ts",
      "surface.ts",
    ]) {
      await expect(exists(join(process.cwd(), "src", "infra", "bases", baseFile))).resolves.toBe(
        true,
      );
    }

    await expect(
      exists(join(process.cwd(), "src", "infra", "assets", "asset_loader.ts")),
    ).resolves.toBe(true);
    await expect(
      exists(join(process.cwd(), "src", "infra", "clients", "http.client.ts")),
    ).resolves.toBe(true);
    await expect(exists(join(process.cwd(), "src", "infra", "clients", "index.ts"))).resolves.toBe(
      true,
    );
    await expect(
      exists(join(process.cwd(), "src", "infra", "clients", "postgres.client.ts")),
    ).resolves.toBe(true);
    await expect(
      exists(join(process.cwd(), "src", "infra", "clients", "redis.client.ts")),
    ).resolves.toBe(true);
    await expect(
      exists(join(process.cwd(), "src", "infra", "files", "file_serializers.ts")),
    ).resolves.toBe(true);
    await expect(
      exists(join(process.cwd(), "src", "infra", "files", "serialized_file_store.ts")),
    ).resolves.toBe(true);
    await expect(exists(join(process.cwd(), "src", "infra", "helpers", "index.ts"))).resolves.toBe(
      true,
    );
  });

  it("defines module entrypoints and isolated capabilities", async () => {
    const modules = ["project", "self"];

    for (const moduleName of modules) {
      await expect(
        exists(join(process.cwd(), "src", "modules", moduleName, `${moduleName}.index.ts`)),
      ).resolves.toBe(true);
      await expect(
        exists(join(process.cwd(), "src", "modules", moduleName, `${moduleName}.config.ts`)),
      ).resolves.toBe(true);
      await expect(
        exists(join(process.cwd(), "src", "modules", moduleName, `${moduleName}.bind.ts`)),
      ).resolves.toBe(true);
      await expect(
        exists(join(process.cwd(), "src", "modules", moduleName, `${moduleName}.surface.ts`)),
      ).resolves.toBe(true);

      for (const surfaceFile of [
        "skill.json",
        "knowledge.json",
        "prompt.json",
        "loop.json",
        "capabilities.json",
      ]) {
        await expect(
          exists(join(process.cwd(), "src", "modules", moduleName, "surface", surfaceFile)),
        ).resolves.toBe(true);
      }
    }

    await expect(
      exists(
        join(
          process.cwd(),
          "src",
          "modules",
          "project",
          "capabilities",
          "doctor",
          "doctor.service.ts",
        ),
      ),
    ).resolves.toBe(true);
    await expect(
      exists(
        join(process.cwd(), "src", "modules", "project", "capabilities", "init", "init.service.ts"),
      ),
    ).resolves.toBe(true);
    await expect(
      exists(
        join(
          process.cwd(),
          "src",
          "modules",
          "project",
          "capabilities",
          "reset",
          "reset.service.ts",
        ),
      ),
    ).resolves.toBe(true);
    await expect(
      exists(
        join(
          process.cwd(),
          "src",
          "modules",
          "self",
          "capabilities",
          "update",
          "update.service.ts",
        ),
      ),
    ).resolves.toBe(true);
  });

  it("binds module test suites in each module contract", () => {
    expect(projectModuleConfig.tests).toEqual({
      include: [
        "src/modules/project/project.surface.test.ts",
        "src/modules/project/capabilities/**/*.test.ts",
      ],
    });
    expect(selfModuleConfig.tests).toEqual({
      include: [
        "src/modules/self/self.surface.test.ts",
        "src/modules/self/capabilities/**/*.test.ts",
      ],
    });
  });

  it("binds modules through the canonical module binding contract", () => {
    const projectResult = createProjectModuleBindings({ appVersion: "0.4.0" });
    const selfResult = createSelfModuleBindings({
      currentVersion: "0.4.0",
      packageName: "agent-devkit",
    });

    expect(projectResult.isOk()).toBe(true);
    expect(selfResult.isOk()).toBe(true);

    const project = projectResult.unwrap();
    const self = selfResult.unwrap();

    expect(project.config).toBe(projectModuleConfig);
    expect(Object.keys(project.capabilities)).toEqual(["doctor", "init", "reset"]);
    expect(project.capabilities.doctor.capability).toMatchObject({
      id: "project.doctor",
      moduleId: "project",
    });
    expect(project.capabilities.init.capability).toMatchObject({
      id: "project.init",
      moduleId: "project",
    });
    expect(project.capabilities.reset.capability).toMatchObject({
      id: "project.reset",
      moduleId: "project",
    });

    expect(self.config).toBe(selfModuleConfig);
    expect(Object.keys(self.capabilities)).toEqual(["update"]);
    expect(self.capabilities.update.capability).toMatchObject({
      id: "self.update",
      moduleId: "self",
    });
  });
});
