import { Result } from "./result";

describe("Result", () => {
  it("maps successful values without touching errors", () => {
    const ok = Result.ok<string, number>(2).map((value) => value * 2);
    const error = Result.fail<string, number>("NOPE").map((value) => value * 2);

    expect(ok.unwrap()).toBe(4);
    expect(error.unwrapError()).toBe("NOPE");
  });

  it("flat maps and maps errors", () => {
    const ok = Result.ok<string, number>(2).flatMap((value) =>
      Result.ok<string, string>(String(value)),
    );
    const error = Result.fail<string, number>("NOPE").mapError((value) => `ERR_${value}`);

    expect(ok.unwrap()).toBe("2");
    expect(error.unwrapError()).toBe("ERR_NOPE");
  });

  it("matches success and error branches", () => {
    const ok = Result.ok<string, number>(2).match({
      ok: (value) => value * 2,
      error: () => 0,
    });
    const error = Result.fail<string, number>("NOPE").match({
      ok: (value) => value * 2,
      error: (value) => value.length,
    });

    expect(ok).toBe(4);
    expect(error).toBe(4);
  });
});
