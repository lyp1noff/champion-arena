import { Bracket, Tournament, TournamentCreate, TournamentUpdate } from "@/lib/interfaces";
import { fetchWithRefresh } from "./api";

const url = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api";

export async function getTournaments(
  page: number = 1,
  limit: number = 10,
  orderBy: string = "id",
  order: "asc" | "desc" = "asc",
  search: string = "",
): Promise<{ data: Tournament[]; total: number; page: number; limit: number }> {
  const res = await fetchWithRefresh(
    `${url}/tournaments?page=${page}&limit=${limit}&order_by=${orderBy}&order=${order}&search=${search}`,
    { cache: "no-store" },
  );

  if (!res.ok) {
    throw new Error("Failed to load tournaments");
  }

  return res.json();
}

export async function getTournamentById(id: number): Promise<Tournament> {
  const res = await fetchWithRefresh(`${url}/tournaments/${id}`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to load tournament");
  }

  return res.json();
}

export async function createTournament(tournamentData: TournamentCreate): Promise<Tournament> {
  const res = await fetchWithRefresh(`${url}/tournaments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(tournamentData),
  });

  if (!res.ok) {
    throw new Error("Error creating tournament");
  }

  return res.json();
}

export async function updateTournament(id: number, updateData: TournamentUpdate): Promise<Tournament> {
  const res = await fetchWithRefresh(`${url}/tournaments/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updateData),
  });

  if (!res.ok) {
    throw new Error("Error updating tournament");
  }

  return res.json();
}

export async function deleteTournament(id: number): Promise<{ success: boolean }> {
  const res = await fetchWithRefresh(`${url}/tournaments/${id}`, { method: "DELETE" });

  if (!res.ok) {
    throw new Error("Error deleting tournament");
  }

  return { success: true };
}

export async function getTournamentBracketsById(id: number, sorted: boolean = true): Promise<Bracket[]> {
  const res = await fetchWithRefresh(`${url}/tournaments/${id}/brackets?sorted=${sorted}`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to load tournament brackets");
  }

  return res.json();
}

export async function downloadTournamentDocx(tournamentId: number): Promise<string> {
  const res = await fetchWithRefresh(`${url}/tournaments/${tournamentId}/export_file`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to export tournament file");
  }

  const data = await res.json();
  return `${url}/${data.filename}`;
}

export async function importCbrFile(tournamentId: number, file: File): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetchWithRefresh(`${url}/tournaments/${tournamentId}/import`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error("Failed to upload cbr file");
  }
}

export async function deleteParticipant(participant_id: number): Promise<void> {
  const response = await fetchWithRefresh(`${url}/tournaments/participants/${participant_id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("Failed to delete participant");
  }

  return await response.json();
}

export async function updateTournamentStatus(tournamentId: number, status: string) {
  const response = await fetchWithRefresh(`${url}/tournaments/${tournamentId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });

  if (!response.ok) {
    throw new Error("Failed to update tournament status");
  }

  return await response.json();
}

export async function startTournament(tournamentId: number) {
  const response = await fetchWithRefresh(`${url}/tournaments/${tournamentId}/start`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to start tournament");
  }

  return await response.json();
}
