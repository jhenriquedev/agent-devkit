import packageJson from "../package.json";

describe("package metadata", () => {
  it("publishes the canonical agent binary", () => {
    expect(packageJson.name).toBe("agent-devkit");
    expect(packageJson.version).toBe("0.3.3");
    expect(packageJson.bin).toEqual({ agent: "./dist/main.js" });
  });

  it("does not run filesystem lifecycle hooks during npm install", () => {
    expect(packageJson.scripts).not.toHaveProperty("preinstall");
    expect(packageJson.scripts).not.toHaveProperty("install");
    expect(packageJson.scripts).not.toHaveProperty("postinstall");
  });

  it("routes module tests through the module test runner", () => {
    expect(packageJson.scripts.test).toBe(
      "npm run test:architecture && npm run test:infra && npm run test:app && npm run test:modules",
    );
    expect(packageJson.scripts["test:modules"]).toBe("tsx scripts/test-modules.ts");
    expect(packageJson.scripts["test:module"]).toBe("tsx scripts/test-modules.ts");
    expect(packageJson.scripts["test:modules:changed"]).toBe(
      "tsx scripts/test-modules.ts --changed",
    );
  });
});
