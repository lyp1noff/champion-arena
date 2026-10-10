import {
  ExternalMatch,
  Tournament,
  CurrentTournamentResponse,
  TatamisResponse,
  Bracket,
  BracketMatch,
  BracketParticipant,
  Athlete,
  SyncTournamentResponse,
  OutboxItem,
  OutboxStatus,
} from "./interfaces";

export const BACKEND_URL = "/api";

export async function getMatch(matchId: string): Promise<ExternalMatch> {
  const response = await fetch(`${BACKEND_URL}/matches/${matchId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch match data");
  }
  return response.json();
}

export async function startMatch(matchId: string): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/matches/${matchId}/start`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to start match");
  }
}

export async function finishMatch(
  matchId: string,
  scoreAthlete1: number,
  scoreAthlete2: number,
  winnerId: number,
): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/matches/${matchId}/finish`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      score_athlete1: scoreAthlete1,
      score_athlete2: scoreAthlete2,
      winner_id: winnerId,
    }),
  });
  if (!response.ok) {
    throw new Error("Failed to finish match");
  }
}

export async function correctMatchResult(
  matchId: string,
  scoreAthlete1: number,
  scoreAthlete2: number,
  winnerId: number,
): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/matches/${matchId}/correct-result`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      score_athlete1: scoreAthlete1,
      score_athlete2: scoreAthlete2,
      winner_id: winnerId,
    }),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail ?? "Failed to correct match result");
  }
}

export async function updateScores(matchId: string, scoreAthlete1: number, scoreAthlete2: number): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/matches/${matchId}/scores`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      score_athlete1: scoreAthlete1,
      score_athlete2: scoreAthlete2,
    }),
  });
  if (!response.ok) {
    throw new Error("Failed to update scores");
  }
}

// Setup API functions
export async function getExternalTournaments(): Promise<Tournament[]> {
  const response = await fetch(`${BACKEND_URL}/external/tournaments`);
  if (!response.ok) {
    throw new Error("Failed to fetch external tournaments");
  }
  const data = await response.json();
  return data || [];
}

export async function getLocalTournaments(): Promise<Tournament[]> {
  const response = await fetch(`${BACKEND_URL}/tournaments`);
  if (!response.ok) {
    throw new Error("Failed to fetch local tournaments");
  }

  const data: Array<Tournament & { external_id: number }> = await response.json();
  return data.map(({ external_id, ...tournament }) => ({
    ...tournament,
    // All Tatami routes and settings use the Arena tournament id.
    id: external_id,
  }));
}

export async function getExternalAthletes(): Promise<Athlete[]> {
  const response = await fetch(`${BACKEND_URL}/external/athletes`);
  if (!response.ok) {
    throw new Error("Failed to fetch athletes");
  }
  return response.json();
}

export async function getCurrentTournament(): Promise<CurrentTournamentResponse> {
  const response = await fetch(`${BACKEND_URL}/settings/current-tournament`);
  if (!response.ok) {
    throw new Error("Failed to fetch current tournament");
  }
  return response.json();
}

export async function setCurrentTournament(tournamentId: number): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/settings/current-tournament`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ current_tournament_id: tournamentId }),
  });
  if (!response.ok) {
    throw new Error("Failed to save tournament selection");
  }
}

export async function getTatamis(tournamentId: number): Promise<TatamisResponse> {
  const response = await fetch(`${BACKEND_URL}/tournaments/${tournamentId}/tatamis`);
  if (!response.ok) {
    throw new Error("Failed to fetch available tatamis");
  }
  const data = await response.json();
  return { tatamis: data.tatamis || [] };
}

export async function syncTournament(tournamentId: number): Promise<SyncTournamentResponse> {
  const response = await fetch(`${BACKEND_URL}/tournaments/${tournamentId}/sync`, {
    method: "POST",
  });
  if (!response.ok) {
    let message = "Failed to sync tournament";
    try {
      const data = await response.json();
      if (typeof data?.detail === "string") {
        message = data.detail;
      }
    } catch {
      // Keep default message if the backend did not return JSON.
    }
    throw new Error(message);
  }
  return response.json();
}

export async function rebootstrapTournament(tournamentId: number): Promise<SyncTournamentResponse> {
  const response = await fetch(`${BACKEND_URL}/tournaments/${tournamentId}/rebootstrap`, {
    method: "POST",
  });
  if (!response.ok) {
    let message = "Failed to rebootstrap tournament";
    try {
      const data = await response.json();
      if (typeof data?.detail === "string") {
        message = data.detail;
      }
    } catch {
      // Keep default message if the backend did not return JSON.
    }
    throw new Error(message);
  }
  return response.json();
}

export async function getOutboxStatus(): Promise<OutboxStatus> {
  const res = await fetch(`${BACKEND_URL}/outbox/status`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to fetch outbox status");
  }
  return res.json();
}

export async function getOutboxItems(
  status: string,
  limit = 50,
  offset = 0,
): Promise<{ total: number; items: OutboxItem[] }> {
  const params = new URLSearchParams({ status, limit: String(limit), offset: String(offset) });
  const response = await fetch(`${BACKEND_URL}/outbox/items?${params}`, { cache: "no-store" });
  if (!response.ok) throw new Error("Failed to fetch outbox items");
  return response.json();
}

export async function getOutboxItem(itemId: number): Promise<OutboxItem> {
  const response = await fetch(`${BACKEND_URL}/outbox/${itemId}`, { cache: "no-store" });
  if (!response.ok) throw new Error("Failed to fetch outbox item");
  return response.json();
}

export async function retryOutboxItem(itemId: number): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/outbox/${itemId}/retry`, { method: "POST" });
  if (!response.ok) throw new Error("Failed to retry outbox item");
}

export async function retryAllOutboxItems(): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/outbox/retry-all`, { method: "POST" });
  if (!response.ok) throw new Error("Failed to retry outbox items");
}

export async function reconcileOutboxItem(itemId: number): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/outbox/${itemId}/reconcile`, { method: "POST" });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail ?? "Failed to reconcile outbox item");
  }
}

// Tatami API functions
export async function getTournament(tournamentId: string): Promise<Tournament> {
  const response = await fetch(`${BACKEND_URL}/tournaments/${tournamentId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch tournament");
  }
  return response.json();
}

export async function getBrackets(tournamentId: string): Promise<Bracket[]> {
  const response = await fetch(`${BACKEND_URL}/tournaments/${tournamentId}/brackets`);
  if (!response.ok) {
    throw new Error("Failed to fetch brackets");
  }
  return response.json();
}

export async function getMatches(bracketId: string): Promise<BracketMatch[]> {
  const response = await fetch(`${BACKEND_URL}/brackets/${bracketId}/matches`);
  if (!response.ok) {
    throw new Error("Failed to fetch matches");
  }
  return response.json();
}

export async function getBracketParticipants(bracketId: number): Promise<BracketParticipant[]> {
  const response = await fetch(`${BACKEND_URL}/brackets/${bracketId}/participants`);
  if (!response.ok) {
    throw new Error("Failed to fetch bracket participants");
  }
  return response.json();
}

export async function addBracketParticipant(
  bracketId: number,
  athleteExternalId: number,
  seed?: number,
): Promise<BracketParticipant> {
  const response = await fetch(`${BACKEND_URL}/brackets/${bracketId}/participants`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      athlete_external_id: athleteExternalId,
      seed,
    }),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail ?? "Failed to add participant");
  }
  return response.json();
}

export async function deleteBracketParticipant(bracketId: number, participantId: number): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/brackets/${bracketId}/participants/${participantId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail ?? "Failed to remove participant");
  }
}

export async function updateBracketParticipantSeed(
  bracketId: number,
  participantId: number,
  seed: number,
): Promise<BracketParticipant> {
  const response = await fetch(`${BACKEND_URL}/brackets/${bracketId}/participants/${participantId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ seed }),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail ?? "Failed to update participant seed");
  }
  return response.json();
}

export async function moveBracketParticipant(
  participantId: number,
  targetBracketId: number,
  targetSeed?: number,
): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/brackets/participants/move`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      participant_id: participantId,
      target_bracket_id: targetBracketId,
      target_seed: targetSeed,
    }),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail ?? "Failed to move participant");
  }
}
