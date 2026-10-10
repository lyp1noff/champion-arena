import { useSyncExternalStore } from "react";
import { ExternalMatch } from "@/lib/interfaces";

export const TIMER_STATUS = { IDLE: "idle", RUNNING: "running", PAUSED: "paused" } as const;
export type TimerStatus = (typeof TIMER_STATUS)[keyof typeof TIMER_STATUS];

export type TatamiState = {
  timerStatus: TimerStatus;
  startTimestamp: number | null;
  pausedElapsed: number;
  durationMs: number;
  score1: number;
  score2: number;
  shido1: number;
  shido2: number;
  senshu: number;
  swap_status: boolean;
  currentMatch: ExternalMatch | null;
  setState: (partial: Partial<TatamiState>) => void;
  reset: () => void;
  setMatch: (match: ExternalMatch, durationMs?: number) => void;
  setDuration: (durationMs: number) => void;
};

const STORAGE_KEY = "tatami-storage";
const listeners = new Set<() => void>();

const defaults = {
  timerStatus: TIMER_STATUS.IDLE,
  startTimestamp: null,
  pausedElapsed: 0,
  durationMs: 60 * 1000,
  score1: 0,
  score2: 0,
  shido1: 0,
  shido2: 0,
  senshu: 0,
  swap_status: false,
  currentMatch: null,
};

function readPersistedState(): Partial<TatamiState> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as { state?: Partial<TatamiState> };
    return parsed.state ?? {};
  } catch {
    return {};
  }
}

let state: TatamiState;

function persistedSnapshot(value: TatamiState) {
  return {
    timerStatus: value.timerStatus,
    startTimestamp: value.startTimestamp,
    pausedElapsed: value.pausedElapsed,
    durationMs: value.durationMs,
    score1: value.score1,
    score2: value.score2,
    shido1: value.shido1,
    shido2: value.shido2,
    senshu: value.senshu,
    swap_status: value.swap_status,
    currentMatch: value.currentMatch,
  };
}

function update(partial: Partial<TatamiState>) {
  state = { ...state, ...partial };
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ state: persistedSnapshot(state), version: 2 }));
  listeners.forEach((listener) => listener());
}

function reset() {
  update({ ...defaults, swap_status: state.swap_status });
}

function setMatch(match: ExternalMatch, durationMs: number = defaults.durationMs) {
  if (match.external_id && state.currentMatch?.external_id === match.external_id) return;
  update({ ...defaults, durationMs, swap_status: state.swap_status, currentMatch: match });
}

state = {
  ...defaults,
  ...readPersistedState(),
  setState: update,
  reset,
  setMatch,
  setDuration: (durationMs: number) => update({ durationMs }),
};

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function useTatamiStoreHook() {
  return useSyncExternalStore(subscribe, () => state, () => state);
}

export const useTatamiStore = Object.assign(useTatamiStoreHook, { setState: update });
