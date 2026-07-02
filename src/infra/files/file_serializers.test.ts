import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  FileSerializerRegistry,
  JsonFileSerializer,
  MarkdownFileSerializer,
  PdfFileSerializer,
  TextFileSerializer,
} from "./file_serializers";
import { SerializedFileStore } from "./serialized_file_store";

describe("file serializers", () => {
  it("serializes and deserializes json, txt, md and pdf payloads", async () => {
    const registry = FileSerializerRegistry.withDefaults();

    const json = await registry.serialize("json", { ok: true });
    const text = await registry.serialize("txt", "plain text");
    const markdown = await registry.serialize("md", "# Title");
    const pdf = await registry.serialize("pdf", Buffer.from("%PDF-1.4\n"));

    expect(json.isOk()).toBe(true);
    expect(text.isOk()).toBe(true);
    expect(markdown.isOk()).toBe(true);
    expect(pdf.isOk()).toBe(true);
    expect(await registry.deserialize("json", json.unwrap())).toMatchObject({
      unwrap: expect.any(Function),
    });
    expect((await registry.deserialize("txt", text.unwrap())).unwrap()).toBe("plain text");
    expect((await registry.deserialize("md", markdown.unwrap())).unwrap()).toBe("# Title");
    const pdfPayload = await registry.deserialize<Uint8Array>("pdf", pdf.unwrap());
    expect(Buffer.from(pdfPayload.unwrap()).toString()).toBe("%PDF-1.4\n");
  });

  it("writes and reads serialized files by extension", async () => {
    const directory = await mkdtemp(join(tmpdir(), "agent-devkit-files-"));
    const store = new SerializedFileStore({
      rootDirectory: directory,
      serializers: new FileSerializerRegistry([
        new JsonFileSerializer(),
        new TextFileSerializer(),
        new MarkdownFileSerializer(),
        new PdfFileSerializer(),
      ]),
    });

    try {
      const write = await store.write("state/config.json", { version: "0.3.3" });
      const read = await store.read<{ version: string }>("state/config.json");

      expect(write.isOk()).toBe(true);
      expect(read.isOk()).toBe(true);
      expect(read.unwrap()).toEqual({ version: "0.3.3" });
      expect(await readFile(join(directory, "state", "config.json"), "utf8")).toContain(
        '"version": "0.3.3"',
      );
    } finally {
      await rm(directory, { force: true, recursive: true });
    }
  });
});
