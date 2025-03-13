import { Athlete, AthleteCreate } from "../interfaces";

const url = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api";

export async function getAthletes(
  page: number = 1,
  limit: number = 10,
  orderBy: string = "last_name",
  order: string = "asc",
  search: string = "",
  coach_search: string = ""
) {
  const res = await fetch(
    `${url}/athletes?page=${page}&limit=${limit}&order_by=${orderBy}&order=${order}&search=${search}&coach_search=${coach_search}`,
    { cache: "no-store" }
  );

  if (!res.ok) {
    throw new Error("Failed to load athletes");
  }

  return res.json();
}

export async function createAthletes(data: AthleteCreate): Promise<Athlete> {
  console.log(data);
  const res = await fetch(`${url}/athletes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new Error("Error creating athlete");
  }

  return res.json();
}
