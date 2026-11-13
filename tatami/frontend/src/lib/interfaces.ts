export const TOURNAMENT_STATUS = {
  DRAFT: "draft",
  UPCOMING: "upcoming",
  STARTED: "started",
  FINISHED: "finished",
} as const;
export type TournamentStatus = (typeof TOURNAMENT_STATUS)[keyof typeof TOURNAMENT_STATUS];

export const BRACKET_STATUS = { PENDING: "pending", STARTED: "started", FINISHED: "finished" } as const;
export type BracketStatus = (typeof BRACKET_STATUS)[keyof typeof BRACKET_STATUS];

export const MATCH_STATUS = { NOT_STARTED: "not_started", STARTED: "started", FINISHED: "finished" } as const;
export type MatchStatus = (typeof MATCH_STATUS)[keyof typeof MATCH_STATUS];

export const SYNC_WORKER_PHASE = {
  STARTING: "starting",
  IDLE: "idle",
  SENDING: "sending",
  OFFLINE: "offline",
  STOPPED: "stopped",
  UNKNOWN: "unknown",
} as const;
export type SyncWorkerPhase = (typeof SYNC_WORKER_PHASE)[keyof typeof SYNC_WORKER_PHASE];

export const BRACKET_SYNC_STATE = { PENDING: "pending", ATTENTION: "attention", SYNCED: "synced" } as const;
export type BracketSyncState = (typeof BRACKET_SYNC_STATE)[keyof typeof BRACKET_SYNC_STATE];

export interface ExternalMatch {
  external_id: string;
  bracket_display_name?: string;
  athlete1?: {
    id: number;
    first_name: string;
    last_name: string;
    gender: string;
    birth_date?: string;
    coaches_last_name: string[];
    age?: number;
  };
  athlete2?: {
    id: number;
    first_name: string;
    last_name: string;
    gender: string;
    birth_date?: string;
    coaches_last_name: string[];
    age?: number;
  };
  winner?: {
    id: number;
    first_name: string;
    last_name: string;
    gender: string;
    birth_date?: string;
    coaches_last_name: string[];
    age?: number;
  };
  score_athlete1?: number;
  score_athlete2?: number;
  status: MatchStatus;
  started_at?: string;
  ended_at?: string;
}

export interface Athlete {
  id: number;
  external_id?: number;
  first_name: string;
  last_name: string;
  gender: string;
  birth_date?: string;
  coaches_last_name: string[] | string;
  age?: number;
}

export interface Match {
  external_id: string;
  round_type?: string;
  stage?: string;
  repechage_side?: string;
  repechage_step?: number;
  athlete1?: Athlete;
  athlete2?: Athlete;
  winner?: Athlete;
  winner_id?: number;
  score_athlete1?: number;
  score_athlete2?: number;
  status: MatchStatus;
  started_at?: string;
  ended_at?: string;
}

export interface BracketMatch {
  external_id: string;
  round_number: number;
  position: number;
  match: Match;
  next_slot?: number;
}

export interface Bracket {
  id?: number;
  external_id: number;
  category: string;
  type: string;
  start_time?: string;
  day?: number;
  tatami?: number;
  group_id?: number;
  display_name?: string;
  status: BracketStatus;
  tournament_id: number;
  participants: Athlete[];
  matches?: BracketMatch[];
}

export interface BracketParticipant {
  id: number;
  bracket_id: number;
  athlete_id?: number | null;
  seed: number;
  athlete?: {
    id: number;
    external_id: number;
    first_name: string;
    last_name: string;
    coaches_last_name: string;
  } | null;
}

export interface Tournament {
  id: number;
  name: string;
  location: string;
  start_date: string;
  end_date: string;
  registration_start_date?: string;
  registration_end_date?: string;
  image_url?: string;
  status?: TournamentStatus;
  description?: string;
}

export interface TournamentMatchesFull {
  category: string;
  type: string;
  start_time?: string;
  tatami?: number;
  group_id?: number;
  display_name?: string;
  status: BracketStatus;
  bracket_id: number;
  matches: BracketMatch[];
}

export interface CurrentTournamentResponse {
  current_tournament_id: number | null;
}

export interface SyncWorkerStatus {
  alive: boolean;
  phase: SyncWorkerPhase;
  heartbeat_at?: string | null;
  last_success_at?: string | null;
  last_error?: string | null;
  next_attempt_at?: string | null;
}

export interface SyncStatus {
  total: number;
  synced: number;
  pending: number;
  attention: number;
  oldest_pending_at?: string | null;
  worker: SyncWorkerStatus;
}

export interface BracketSyncItem {
  bracket_id: number;
  name: string;
  tournament_name: string;
  status?: string | null;
  state: BracketSyncState;
  version: number;
  synced_version?: number | null;
  synced_at?: string | null;
  updated_at?: string | null;
  error?: string | null;
  remote_version?: number | null;
}

export interface TatamisResponse {
  tatamis: number[];
}

export interface SyncTournamentResponse {
  status: string;
  message?: string;
}
