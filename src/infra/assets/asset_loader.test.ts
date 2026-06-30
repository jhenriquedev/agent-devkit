import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { AssetLoader } from "./asset_loader";

describe("AssetLoader", () => {
  it("loads i18n text/json assets and binary image/font assets", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-assets-"));

    try {
      await mkdir(join(root, "i18n"), { recursive: true });
      await mkdir(join(root, "images"), { recursive: true });
      await mkdir(join(root, "fonts"), { recursive: true });
      await writeFile(join(root, "i18n", "pt-BR.json"), JSON.stringify({ hello: "ola" }));
      await writeFile(join(root, "i18n", "help.md"), "# Ajuda");
      await writeFile(join(root, "images", "logo.bin"), Buffer.from([1, 2, 3]));
      await writeFile(join(root, "fonts", "brand.bin"), Buffer.from([4, 5, 6]));

      const loader = new AssetLoader({ rootDirectory: root });
      const messages = await loader.loadJson<{ hello: string }>("i18n", "pt-BR.json");
      const help = await loader.loadText("i18n", "help.md");
      const image = await loader.loadBinary("images", "logo.bin");
      const font = await loader.loadBinary("fonts", "brand.bin");

      expect(messages.isOk()).toBe(true);
      expect(help.isOk()).toBe(true);
      expect(image.isOk()).toBe(true);
      expect(font.isOk()).toBe(true);
      expect(messages.unwrap()).toEqual({ hello: "ola" });
      expect(help.unwrap()).toBe("# Ajuda");
      expect([...image.unwrap()]).toEqual([1, 2, 3]);
      expect([...font.unwrap()]).toEqual([4, 5, 6]);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("rejects asset paths that escape the configured asset root", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-assets-"));

    try {
      const loader = new AssetLoader({ rootDirectory: root });
      const result = await loader.loadText("i18n", "../secret.txt");

      expect(result.isErr()).toBe(true);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });
});
