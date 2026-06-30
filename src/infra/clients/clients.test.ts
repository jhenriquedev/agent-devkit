import type { DatabaseRow } from "../bases/database";
import { PostgresClient } from "./postgres.client";
import { RedisClient } from "./redis.client";

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
});
