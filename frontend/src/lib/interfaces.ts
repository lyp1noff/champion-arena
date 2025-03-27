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
  start_date: Date;
  end_date: Date;
  registration_start_date: Date;
  registration_end_date: Date;
  image_url: string;
}
export type TournamentCreate = Omit<Tournament, "id" | "status">;
export type TournamentUpdate = Partial<TournamentCreate>;

export type Participant = {
  seed: number;
  last_name: string;
  first_name: string;
};

export type Bracket = {
  id: number;
  tournament_id: number;
  category: string;
  participants: Participant[];
};

export interface Coach {
  id: number;
  name: string;
  last_name: string;
}

export type BracketMatchAthlete = {
  id: number;
  first_name: string;
  last_name: string;
};

export type BracketMatch = {
  id: number;
  round_number: number;
  position: number;
  athlete1: BracketMatchAthlete | null;
  athlete2: BracketMatchAthlete | null;
  winner: BracketMatchAthlete | null;
  score_athlete1: number | null;
  score_athlete2: number | null;
  is_finished: boolean;
};

export type BracketMatches = BracketMatch[];
