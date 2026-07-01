import type { DatabaseRow } from "../bases/database";
import { FetchHttpClient } from "./http.client";
import { PostgresClient } from "./postgres.client";
import { RedisClient } from "./redis.client";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
});

describe("HTTP infra client", () => {
  it("reads JSON responses from successful HTTP requests", async () => {
    globalThis.fetch = async () => new Response(JSON.stringify({ ok: true }), { status: 200 });
    const client = new FetchHttpClient({ timeoutMs: 100 });

    const result = await client.getJson<{ ok: boolean }>("https://example.test/status");

    expect(result.isOk()).toBe(true);
    expect(result.unwrap()).toEqual({ body: { ok: true }, status: 200 });
  });

  it("returns Result failures for non-success HTTP status codes", async () => {
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ error: "failed" }), { status: 500 });
    const client = new FetchHttpClient({ timeoutMs: 100 });

    const result = await client.getJson("https://example.test/status");

    expect(result.isErr()).toBe(true);
  });
});

describe("database infra clients", () => {
  it("reads Postgres rows through an injected query executor", async () => {
    const client = new PostgresClient({
      query: async <TRow extends DatabaseRow>() => ({
        rows: [{ id: "project", enabled: true } as unknown as TRow],
      }),
    });

    const result = await client.queryRows<{ id: string; enabled: boolean }>({
      sql: "select id, enabled from modules where id = $1",
      values: ["project"],
    });

    expect(result.isOk()).toBe(true);
    expect(result.unwrap()).toEqual([{ id: "project", enabled: true }]);
  });

  it("reads Redis values through an injected key-value executor", async () => {
    const client = new RedisClient({
      get: async (key) => (key === "agent:locale" ? "pt-BR" : null),
      hGetAll: async () => ({ theme: "dark", accent: "violet" }),
    });

    const value = await client.getString("agent:locale");
    const hash = await client.getHash("agent:theme");

    expect(value.isOk()).toBe(true);
    expect(hash.isOk()).toBe(true);
    expect(value.unwrap()).toBe("pt-BR");
    expect(hash.unwrap()).toEqual({ theme: "dark", accent: "violet" });
  });

  it("returns Result failures when database executors throw", async () => {
    const postgres = new PostgresClient({
      query: async () => {
        throw new Error("connection failed");
      },
    });
    const redis = new RedisClient({
      get: async () => {
        throw new Error("connection failed");
      },
      hGetAll: async () => {
        throw new Error("connection failed");
      },
    });

    expect((await postgres.queryRows({ sql: "select 1" })).isErr()).toBe(true);
    expect((await redis.getString("missing")).isErr()).toBe(true);
  });

  it("returns Result failures when database executors time out", async () => {
    const never = new Promise<never>(() => undefined);
    const postgres = new PostgresClient(
      {
        query: async () => never,
      },
      { timeoutMs: 1 },
    );
    const redis = new RedisClient(
      {
        get: async () => never,
        hGetAll: async () => never,
      },
      { timeoutMs: 1 },
    );

    expect((await postgres.queryRows({ sql: "select 1" })).isErr()).toBe(true);
    expect((await redis.getString("missing")).isErr()).toBe(true);
    expect((await redis.getHash("missing")).isErr()).toBe(true);
  });
});
