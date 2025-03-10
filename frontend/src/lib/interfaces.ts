export interface Athlete {
  id: number;
  last_name: string;
  first_name: string;
  gender: string;
  birthdate: string;
  age: string;
  coach_id: number;
  coach_last_name: number;
}

export interface Tournament {
  id: number;
  name: string;
  location: string;
  status: string;
  start_date: Date;
  end_date: Date;
  registration_start_date: Date;
  registration_end_date: Date;
}
