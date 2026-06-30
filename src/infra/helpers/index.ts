export function isDefined<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined;
}

export function unique<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

export { SurfaceLoader } from "./surface_loader";
