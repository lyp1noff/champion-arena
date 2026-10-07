export const DEFAULT_MATCH_DURATION_MS = 60_000;

export const MATCH_DURATION_PRESETS = [
  { label: "0:30", durationMs: 30_000 },
  { label: "0:45", durationMs: 45_000 },
  { label: "1:00", durationMs: 60_000 },
  { label: "1:30", durationMs: 90_000 },
  { label: "2:00", durationMs: 120_000 },
  { label: "3:00", durationMs: 180_000 },
] as const;

function storageKey(tatamiId: string): string {
  return `tatami-${tatamiId}-default-duration-ms`;
}

export function readDefaultMatchDuration(tatamiId: string): number {
  const stored = Number(localStorage.getItem(storageKey(tatamiId)));
  return Number.isFinite(stored) && stored > 0 ? stored : DEFAULT_MATCH_DURATION_MS;
}

export function writeDefaultMatchDuration(tatamiId: string, durationMs: number): void {
  localStorage.setItem(storageKey(tatamiId), String(durationMs));
}
