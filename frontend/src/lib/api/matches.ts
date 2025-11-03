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
