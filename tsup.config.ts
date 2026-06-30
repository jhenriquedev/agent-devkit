import { defineConfig } from "tsup";

export default defineConfig({
  clean: true,
  dts: false,
  entry: ["src/main.tsx"],
  format: ["esm"],
  minify: false,
  outDir: "dist",
  platform: "node",
  shims: false,
  sourcemap: true,
  splitting: false,
  target: "node20",
});
