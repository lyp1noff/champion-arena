import { BACKEND_URL } from "@/lib/config";

import { fetchWithRefresh } from "./api";

export async function updateMatchStatus(matchId: string, status: string) {
  const response = await fetchWithRefresh(`${BACKEND_URL}/matches/${matchId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });

  if (!response.ok) {
    throw new Error("Failed to update match status");
  }

  return await response.json();
}

export async function startMatch(matchId: string) {
  const response = await fetchWithRefresh(`${BACKEND_URL}/matches/${matchId}/start`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to start match");
  }
  return await response.json();
}

export async function finishMatch(
  matchId: string,
  payload: { score_athlete1: number; score_athlete2: number; winner_id: number },
) {
  const response = await fetchWithRefresh(`${BACKEND_URL}/matches/${matchId}/finish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to finish match");
  }
  return await response.json();
}

export async function updateMatchScores(
  matchId: string,
  payload: { score_athlete1?: number; score_athlete2?: number },
) {
  const response = await fetchWithRefresh(`${BACKEND_URL}/matches/${matchId}/scores`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to update scores");
  }
  return await response.json();
}
