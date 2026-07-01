import { access, readdir } from "node:fs/promises";
import { join } from "node:path";
import { agentModuleDefinitions } from "./modules/modules.registry";

const moduleOptions = {
  appVersion: "0.4.0",
  currentVersion: "0.4.0",
  packageName: "agent-devkit",
};

async function exists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

function capabilityDirectory(capabilityId: string): { capabilityName: string; moduleId: string } {
  const [moduleId, capabilityName] = capabilityId.split(".");

  if (moduleId === undefined || capabilityName === undefined) {
    throw new Error(`Invalid capability id: ${capabilityId}`);
  }

  return { capabilityName, moduleId };
}

describe("canonical architecture", () => {
  it("does not keep a root tests directory", async () => {
    await expect(readdir(join(process.cwd(), "tests"))).rejects.toThrow();
  });

  it("keeps shared assets in canonical folders", async () => {
    for (const assetDirectory of ["i18n", "images", "fonts", "themes"]) {
      await expect(
        exists(join(process.cwd(), "src", "assets", assetDirectory, ".gitkeep")),
      ).resolves.toBe(true);
    }
  });

  it("keeps global infra bases available", async () => {
    for (const baseFile of [
      "assets.ts",
      "bind.ts",
      "capability.ts",
      "config.ts",
      "crypto.ts",
      "database.ts",
      "dependency.ts",
      "errors.ts",
      "i18n.ts",
      "logger.ts",
      "module.ts",
      "result.ts",
      "serializer.ts",
      "surface.ts",
      "theme.ts",
      "tool_runtime.ts",
    ]) {
      await expect(exists(join(process.cwd(), "src", "infra", "bases", baseFile))).resolves.toBe(
        true,
      );
    }

    for (const infraFile of [
      ["assets", "asset_loader.ts"],
      ["assets", "i18n_catalog.ts"],
      ["clients", "http.client.ts"],
      ["clients", "postgres.client.ts"],
      ["clients", "redis.client.ts"],
      ["crypto", "encrypted_secret_store.ts"],
      ["crypto", "local_secret_crypto.ts"],
      ["files", "file_serializers.ts"],
      ["files", "serialized_file_store.ts"],
      ["helpers", "index.ts"],
    ]) {
      await expect(exists(join(process.cwd(), "src", "infra", ...infraFile))).resolves.toBe(true);
    }
  });

  it("defines module entrypoints, surfaces and isolated capabilities", async () => {
    for (const definition of agentModuleDefinitions) {
      const moduleName = definition.id;
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

      for (const surfaceFile of ["skill.json", "knowledge.json", "prompt.json", "loop.json"]) {
        await expect(
          exists(join(process.cwd(), "src", "modules", moduleName, "surface", surfaceFile)),
        ).resolves.toBe(true);
      }

      const binding = definition.bind(moduleOptions);
      expect(binding.isOk()).toBe(true);

      for (const capability of definition.capabilities(binding.unwrap())) {
        const { capabilityName, moduleId } = capabilityDirectory(capability.capability.id);
        await expect(
          exists(
            join(
              process.cwd(),
              "src",
              "modules",
              moduleId,
              "capabilities",
              capabilityName,
              `${capabilityName}.service.ts`,
            ),
          ),
        ).resolves.toBe(true);
      }
    }
  });

  it("binds module test suites in each module contract", () => {
    for (const definition of agentModuleDefinitions) {
      expect(definition.config.tests.include).toEqual([
        `src/modules/${definition.id}/${definition.id}.surface.test.ts`,
        `src/modules/${definition.id}/capabilities/**/*.test.ts`,
      ]);
    }
  });

  it("binds modules through the canonical module binding contract", () => {
    for (const definition of agentModuleDefinitions) {
      const binding = definition.bind(moduleOptions);

      expect(binding.isOk()).toBe(true);
      expect(definition.config.id).toBe(definition.id);

      const capabilities = definition.capabilities(binding.unwrap());
      expect(capabilities.length).toBeGreaterThan(0);

      for (const capability of capabilities) {
        expect(capability.capability.moduleId).toBe(definition.id);
        expect(capability.capability.id).toMatch(new RegExp(`^${definition.id}\\.`));
        expect(capability.inputSchema).toBeDefined();
        expect(capability.outputSchema).toBeDefined();
      }
    }
  });
});
