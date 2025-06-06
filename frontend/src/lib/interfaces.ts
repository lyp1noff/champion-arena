export interface Athlete {
  id: number;
  last_name: string;
  first_name: string;
  gender: string;
  birth_date: string;
  age: string;
  coach_id: number;
  coach_last_name: number;
}

export type AthleteCreate = Omit<Athlete, "id" | "coach_last_name" | "age">;
export type AthleteUpdate = Partial<AthleteCreate>;

export interface Tournament {
  id: number;
  name: string;
  location: string;
  // status: string;
  start_date: string;
  end_date: string;
  registration_start_date: string;
  registration_end_date: string;
  image_url: string;
}

export type TournamentCreate = Omit<Tournament, "id" | "status">;
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

export interface Category {
  id: number;
  name: string;
  age: number;
  gender: string; //"male" | "female" | "any";
}

export type Participant = {
  seed: number;
  last_name: string;
  first_name: string;
  coach_last_name: string;
};

export type BracketType = "round_robin" | "single_elimination";
export type Bracket = {
  id: number;
  tournament_id: number;
  category: string;
  type: BracketType;
  start_time: string;
  tatami: number;
  participants: Participant[];
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
  coach_last_name: string;
};

export type RoundType = "final" | "semifinal" | "quarterfinal" | "";

export type Match = {
  id: number;
  round_type: RoundType;
  athlete1: BracketMatchAthlete | null;
  athlete2: BracketMatchAthlete | null;
  winner: BracketMatchAthlete | null;
  score_athlete1: number | null;
  score_athlete2: number | null;
  is_finished: boolean;
};

export type BracketMatch = {
  id: number;
  round_number: number;
  position: number;
  match: Match;
};

export type BracketMatches = BracketMatch[];

// export type BracketWithCategory = {
//   bracket_id: number;
//   category: string;
//   matches: BracketMatch[];
// };
