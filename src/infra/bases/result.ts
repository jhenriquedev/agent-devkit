export class Result<Left, Right> {
  readonly #left?: Left;
  readonly #right?: Right;
  readonly #ok: boolean;

  private constructor(ok: boolean, left?: Left, right?: Right) {
    this.#ok = ok;
    this.#left = left;
    this.#right = right;
  }

  static ok<Left, Right>(right: Right): Result<Left, Right> {
    return new Result<Left, Right>(true, undefined, right);
  }

  static fail<Left, Right>(left: Left): Result<Left, Right> {
    return new Result<Left, Right>(false, left);
  }

  isOk(): boolean {
    return this.#ok;
  }

  isErr(): boolean {
    return !this.#ok;
  }

  flatMap<NextRight>(mapper: (right: Right) => Result<Left, NextRight>): Result<Left, NextRight> {
    return this.#ok ? mapper(this.#right as Right) : Result.fail(this.#left as Left);
  }

  map<NextRight>(mapper: (right: Right) => NextRight): Result<Left, NextRight> {
    return this.#ok ? Result.ok(mapper(this.#right as Right)) : Result.fail(this.#left as Left);
  }

  mapError<NextLeft>(mapper: (left: Left) => NextLeft): Result<NextLeft, Right> {
    return this.#ok ? Result.ok(this.#right as Right) : Result.fail(mapper(this.#left as Left));
  }

  match<TOutput>(handlers: {
    error: (left: Left) => TOutput;
    ok: (right: Right) => TOutput;
  }): TOutput {
    return this.#ok ? handlers.ok(this.#right as Right) : handlers.error(this.#left as Left);
  }

  unwrap(): Right {
    if (!this.#ok) {
      throw new Error("Cannot unwrap a failed Result");
    }

    return this.#right as Right;
  }

  unwrapError(): Left {
    if (this.#ok) {
      throw new Error("Cannot unwrapError an ok Result");
    }

    return this.#left as Left;
  }
}
