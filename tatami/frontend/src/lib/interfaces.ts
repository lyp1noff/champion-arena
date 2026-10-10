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
  status: "not_started" | "started" | "finished";
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
  status: "not_started" | "started" | "finished";
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
  status: string;
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
  status?: string;
  description?: string;
}

export interface TournamentMatchesFull {
  category: string;
  type: string;
  start_time?: string;
  tatami?: number;
  group_id?: number;
  display_name?: string;
  status: string;
  bracket_id: number;
  matches: BracketMatch[];
}

export interface CurrentTournamentResponse {
  current_tournament_id: number | null;
}

export interface OutboxWorkerStatus {
  alive: boolean;
  status: string;
  heartbeat_at?: string | null;
  last_success_at?: string | null;
  last_error?: string | null;
  circuit_open_until?: string | null;
}

export interface OutboxStatus {
  total: number;
  pending: number;
  succeeded: number;
  processing: number;
  retry_wait: number;
  dead_letter: number;
  outstanding: number;
  oldest_pending_at?: string | null;
  worker: OutboxWorkerStatus;
}

export interface OutboxItem {
  id: number;
  tournament_id?: number | null;
  tournament_name?: string | null;
  match_id?: number | null;
  status: string;
  retry_count: number;
  failure_kind?: string | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
  last_attempt_at?: string | null;
  next_attempt_at?: string | null;
  lease_until?: string | null;
  resolved_at?: string | null;
  edge_id?: string | null;
  external_tournament_id?: number | null;
  event_id?: string | null;
  seq?: number | null;
  item_type?: string | null;
  aggregate_id?: string | null;
  aggregate_version?: number | null;
  payload?: unknown;
}

export interface TatamisResponse {
  tatamis: number[];
}

export interface SyncTournamentResponse {
  status: string;
  message?: string;
}

// export interface OutboxStatusResponse {
//   [key: string]: any;
// }
