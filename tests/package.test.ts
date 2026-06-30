import packageJson from "../package.json";

describe("package metadata", () => {
  it("publishes the canonical agent binary", () => {
    expect(packageJson.name).toBe("agent-devkit");
    expect(packageJson.version).toBe("0.4.0");
    expect(packageJson.bin).toEqual({ agent: "./dist/main.js" });
  });

  it("does not run filesystem lifecycle hooks during npm install", () => {
    expect(packageJson.scripts).not.toHaveProperty("preinstall");
    expect(packageJson.scripts).not.toHaveProperty("install");
    expect(packageJson.scripts).not.toHaveProperty("postinstall");
  });
});
