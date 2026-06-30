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
