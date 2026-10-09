export const DEFAULT_MATCH_DURATION_MS = 60_000;
export const SELECTED_TATAMI_STORAGE_KEY = "selected-tatami-id";

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

function tournamentSettingKey(tatamiId: string, tournamentId: number, setting: string): string {
  return `tatami-${tatamiId}-tournament-${tournamentId}-${setting}`;
}

export function readDefaultMatchDuration(tatamiId: string): number {
  const stored = Number(localStorage.getItem(storageKey(tatamiId)));
  return Number.isFinite(stored) && stored > 0 ? stored : DEFAULT_MATCH_DURATION_MS;
}

export function writeDefaultMatchDuration(tatamiId: string, durationMs: number): void {
  localStorage.setItem(storageKey(tatamiId), String(durationMs));
}

export function readSelectedTatamiId(): string | null {
  return localStorage.getItem(SELECTED_TATAMI_STORAGE_KEY);
}

export function writeSelectedTatamiId(tatamiId: string): void {
  localStorage.setItem(SELECTED_TATAMI_STORAGE_KEY, tatamiId);
}

export function readSelectedDay(tatamiId: string, tournamentId: number): number | null {
  const stored = Number(localStorage.getItem(tournamentSettingKey(tatamiId, tournamentId, "selected-day")));
  return Number.isInteger(stored) && stored > 0 ? stored : null;
}

export function writeSelectedDay(tatamiId: string, tournamentId: number, day: number): void {
  localStorage.setItem(tournamentSettingKey(tatamiId, tournamentId, "selected-day"), String(day));
}

export function readSelectedBracket(tatamiId: string, tournamentId: number, day: number): string | null {
  return localStorage.getItem(tournamentSettingKey(tatamiId, tournamentId, `day-${day}-selected-bracket`));
}

export function writeSelectedBracket(tatamiId: string, tournamentId: number, day: number, bracketId: string): void {
  localStorage.setItem(tournamentSettingKey(tatamiId, tournamentId, `day-${day}-selected-bracket`), bracketId);
}
