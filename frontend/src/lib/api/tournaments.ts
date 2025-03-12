import { Bracket, Tournament, TournamentCreate, TournamentUpdate } from "@/lib/interfaces";

const url = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api";

export async function getTournaments(
  page: number = 1,
  limit: number = 10,
  orderBy: string = "id",
  order: "asc" | "desc" = "asc",
  search: string = ""
): Promise<{ data: Tournament[]; total: number; page: number; limit: number }> {
  const res = await fetch(
    `${url}/tournaments?page=${page}&limit=${limit}&order_by=${orderBy}&order=${order}&search=${search}`,
    { cache: "no-store" }
  );

  if (!res.ok) {
    throw new Error("Ошибка загрузки данных");
  }

  return res.json();
}

export async function getTournamentById(id: number): Promise<Tournament> {
  const res = await fetch(`${url}/tournaments/${id}`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Ошибка загрузки турнира");
  }

  return res.json();
}

export async function createTournament(tournamentData: TournamentCreate): Promise<Tournament> {
  const res = await fetch(`${url}/tournaments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(tournamentData),
  });

  if (!res.ok) {
    throw new Error("Ошибка при создании турнира");
  }

  return res.json();
}

export async function updateTournament(id: number, updateData: TournamentUpdate): Promise<Tournament> {
  const res = await fetch(`${url}/tournaments/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updateData),
  });

  if (!res.ok) {
    throw new Error("Ошибка при обновлении турнира");
  }

  return res.json();
}

export async function deleteTournament(id: number): Promise<{ success: boolean }> {
  const res = await fetch(`${url}/tournaments/${id}`, { method: "DELETE" });

  if (!res.ok) {
    throw new Error("Ошибка при удалении турнира");
  }

  return { success: true };
}

export async function getTournamentBracketsById(id: number): Promise<Bracket[]> {
  const res = await fetch(`${url}/tournaments/${id}/brackets`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Ошибка загрузки турнира");
  }

  return res.json();
}
