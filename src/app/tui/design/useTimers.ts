import { useEffect, useRef, useState } from "react";

export function useInterval(callback: () => void, delayMs: number | null): void {
  const saved = useRef(callback);
  saved.current = callback;

  useEffect(() => {
    if (delayMs === null) {
      return;
    }

    const id = setInterval(() => saved.current(), delayMs);
    return () => clearInterval(id);
  }, [delayMs]);
}

export function useBlink(periodMs = 3600, durationMs = 150): boolean {
  const [blinking, setBlinking] = useState(false);

  useInterval(() => {
    setBlinking(true);
    setTimeout(() => setBlinking(false), durationMs);
  }, periodMs);

  return blinking;
}
