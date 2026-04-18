export const TOURNAMENT_STATUS = {
  DRAFT: "draft",
  UPCOMING: "upcoming",
  STARTED: "started",
  FINISHED: "finished",
} as const;

export type TOURNAMENT_STATUS = (typeof TOURNAMENT_STATUS)[keyof typeof TOURNAMENT_STATUS];

export const ROUND_TYPE = {
  FINAL: "final",
  SEMIFINAL: "semifinal",
  QUARTERFINAL: "quarterfinal",
  ROUND: "round",
} as const;

export type ROUND_TYPE = (typeof ROUND_TYPE)[keyof typeof ROUND_TYPE];

export const MATCH_STATUS = {
  NOT_STARTED: "not_started",
  STARTED: "started",
  FINISHED: "finished",
} as const;

export type MATCH_STATUS = (typeof MATCH_STATUS)[keyof typeof MATCH_STATUS];

export const BRACKET_STATUS = {
  PENDING: "pending",
  STARTED: "started",
  FINISHED: "finished",
} as const;

export type BRACKET_STATUS = (typeof BRACKET_STATUS)[keyof typeof BRACKET_STATUS];

export interface Athlete {
  id: number;
  last_name: string;
  first_name: string;
  gender: string;
  birth_date: string;
  age: string;
  coaches_id: number[];
  coaches_last_name: string[];
}

export type AthleteCreate = Omit<Athlete, "id" | "coaches_last_name" | "age">;
export type AthleteUpdate = Partial<AthleteCreate>;

export interface Tournament {
  id: number;
  name: string;
  location: string;
  status: TOURNAMENT_STATUS;
  start_date: string;
  end_date: string;
  registration_start_date: string;
  registration_end_date: string;
  image_url: string;
}

export type TournamentCreate = Omit<Tournament, "id" | "status" | "image_url"> & {
  image_url?: string;
};

export type TournamentUpdate = Partial<TournamentCreate>;

export interface Application {
  athlete_id: number;
  category_id: number;
  tournament_id: number;
}

export interface ApplicationResponse extends Application {
  id: number;
  status: string;
  athlete: Athlete;
  category: Category;
}

export type Participant = {
  id: number;
  athlete_id: number;
  seed: number;
  last_name: string;
  first_name: string;
  coaches_last_name: string[];
};

export type BracketType = "round_robin" | "single_elimination";
export type Bracket = {
  id: number;
  tournament_id: number;
  category: string;
  type: BracketType;
  group_id?: number;
  display_name?: string;
  status: BRACKET_STATUS;
  participants: Participant[];
  place_1?: BracketMatchAthlete | null;
  place_2?: BracketMatchAthlete | null;
  place_3_a?: BracketMatchAthlete | null;
  place_3_b?: BracketMatchAthlete | null;
};
export type BracketUpdate = Partial<Bracket>;

export interface Coach {
  id: number;
  name: string;
  last_name: string;
}

export type BracketMatchAthlete = {
  id: number;
  first_name: string;
  last_name: string;
  coaches_last_name: string[];
};

export type Match = {
  id: string;
  round_type: ROUND_TYPE | string;
  stage?: "main" | "repechage";
  repechage_side?: "A" | "B" | null;
  repechage_step?: number | null;
  athlete1: BracketMatchAthlete | null;
  athlete2: BracketMatchAthlete | null;
  winner: BracketMatchAthlete | null;
  score_athlete1: number | null;
  score_athlete2: number | null;
  status: MATCH_STATUS;
  started_at?: string | null;
  ended_at?: string | null;
};

export type BracketMatch = {
  id: string;
  round_number: number;
  position: number;
  match: Match;
};

export type BracketMatches = BracketMatch[];

export type BracketMatchesFull = {
  category: string;
  type: BracketType;
  group_id?: number;
  display_name?: string;
  status: BRACKET_STATUS;
  bracket_id: number;
  matches: BracketMatch[];
};

export interface Category {
  id: number;
  name: string;
  min_age: number;
  max_age: number;
  gender: "male" | "female" | "any";
}

export type CategoryCreate = Omit<Category, "id">;

export interface ParticipantMove {
  participant_id: number;
  from_bracket_id: number;
  to_bracket_id: number;
}

export interface ParticipantReorder {
  bracket_id: number;
  participant_updates: Array<{ participant_id: number; new_seed: number }>;
}

export interface BracketCreate {
  tournament_id: number;
  category_id: number;
  group_id?: number;
  type?: string;
}

export interface BracketDelete {
  target_bracket_id?: number;
}

export type TimetableEntryType = "bracket" | "break" | "custom";

export interface TimetableEntry {
  id: number;
  tournament_id: number;
  entry_type: TimetableEntryType;
  day: number;
  tatami: number;
  start_time: string;
  end_time: string;
  order_index: number;
  title?: string | null;
  notes?: string | null;
  bracket_id?: number | null;
  bracket_display_name?: string | null;
  bracket_type?: BracketType | null;
}

// export interface CategoryCreate {
//   name: string;
//   age: number;
//   gender: string;
// }

// export type BracketWithCategory = {
//   bracket_id: number;
//   category: string;
//   matches: BracketMatch[];
// };
