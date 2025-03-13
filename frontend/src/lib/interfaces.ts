export interface Athlete {
  id: number;
  last_name: string;
  first_name: string;
  gender: string;
  birth_date: Date;
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
  category: string;
  participants: Participant[];
};

export interface Coach {
  id: number;
  name: string;
  last_name: string;
}
