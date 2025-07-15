import { Bracket, BracketMatches, BracketUpdate } from "../interfaces";
import { fetchWithRefresh } from "./api";

const url = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api";

export async function getBracketsById(id: number): Promise<Bracket> {
  const res = await fetchWithRefresh(`${url}/brackets/${id}`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to load bracket");
  }

  return res.json();
}

export async function getBracketMatchesById(id: number): Promise<BracketMatches> {
  const res = await fetchWithRefresh(`${url}/brackets/${id}/matches`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to load bracket");
  }

  return res.json();
}

export async function updateBracket(bracketId: number, updateData: BracketUpdate) {
  const response = await fetchWithRefresh(`${url}/brackets/${bracketId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updateData),
  });

  if (!response.ok) {
    throw new Error("Failed to update bracket");
  }

  return await response.json();
}

export async function regenerateBracket(bracketId: number) {
  const response = await fetchWithRefresh(`${url}/brackets/${bracketId}/regenerate`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to regenerate bracket");
  }

  return await response.json();
}

export async function moveParticipant(athleteId: number, fromBracketId: number, toBracketId: number, newSeed: number) {
  const response = await fetchWithRefresh(`${url}/brackets/participants/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      athlete_id: athleteId,
      from_bracket_id: fromBracketId,
      to_bracket_id: toBracketId,
      new_seed: newSeed,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to move participant");
  }

  return await response.json();
}

export async function reorderParticipants(
  bracketId: number,
  participantUpdates: Array<{ athlete_id: number; new_seed: number }>,
) {
  const response = await fetchWithRefresh(`${url}/brackets/participants/reorder`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      bracket_id: bracketId,
      participant_updates: participantUpdates,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to reorder participants");
  }

  return await response.json();
}

export async function createBracket(bracketData: {
  tournament_id: number;
  category_id: number;
  group_id?: number;
  type?: string;
  start_time?: string;
  tatami?: number;
}) {
  const response = await fetchWithRefresh(`${url}/brackets/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bracketData),
  });

  if (!response.ok) {
    throw new Error("Failed to create bracket");
  }

  return await response.json();
}

export async function getCategories() {
  const response = await fetchWithRefresh(`${url}/categories`);

  if (!response.ok) {
    throw new Error("Failed to fetch categories");
  }

  return await response.json();
}

export async function createCategory(categoryData: { name: string; age: number; gender: string }) {
  const response = await fetchWithRefresh(`${url}/categories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(categoryData),
  });

  if (!response.ok) {
    throw new Error("Failed to create category");
  }

  return await response.json();
}
