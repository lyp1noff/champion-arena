import { Athlete, AthleteCreate, AthleteUpdate } from "../interfaces";
import { fetchWithRefresh } from "./api";

const url = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api";

export async function getAthletes(
  page: number = 1,
  limit: number = 10,
  orderBy: string = "last_name",
  order: string = "asc",
  search: string = "",
  coach_search: string = "",
) {
  const res = await fetchWithRefresh(
    `${url}/athletes?page=${page}&limit=${limit}&order_by=${orderBy}&order=${order}&search=${search}&coach_search=${coach_search}`,
    { cache: "no-store" },
  );

  if (!res.ok) {
    throw new Error("Failed to load athletes");
  }

  return res.json();
}

export async function createAthlete(data: AthleteCreate): Promise<Athlete> {
  const res = await fetchWithRefresh(`${url}/athletes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new Error("Error creating athlete");
  }

  return res.json();
}

export async function getAllAthletes(): Promise<Athlete[]> {
  const res = await fetchWithRefresh(`${url}/athletes/all`, { cache: "no-store" });

  if (!res.ok) throw new Error("Failed to load athletes");

  return res.json();
}

export async function getAthleteById(id: number): Promise<Athlete> {
  const res = await fetchWithRefresh(`${url}/athletes/${id}`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to load athlete");
  }

  return res.json();
}

export async function updateAthlete(id: number, data: AthleteUpdate): Promise<Athlete> {
  const res = await fetchWithRefresh(`${url}/athletes/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new Error("Error updating athlete");
  }

  return res.json();
}

export async function deleteAthlete(id: number): Promise<{ success: boolean }> {
  const res = await fetchWithRefresh(`${url}/athletes/${id}`, { method: "DELETE" });

  if (!res.ok) {
    throw new Error("Error deleting athlete");
  }

  return { success: true };
}
