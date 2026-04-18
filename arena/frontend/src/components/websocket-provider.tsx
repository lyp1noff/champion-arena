"use client";

import React from "react";

import { useWebSocket } from "@/hooks/use-websocket";

interface MatchUpdate {
  match_id: string;
  score_athlete1: number | null;
  score_athlete2: number | null;
  status: string | null;
}

interface WebSocketProviderProps {
  children: React.ReactNode;
  tournamentId: string;
  onAnyUpdate?: (update: MatchUpdate) => void;
}

export function WebSocketProvider({ children, tournamentId, onAnyUpdate }: WebSocketProviderProps) {
  const handleMatchUpdate = React.useCallback(
    (update: MatchUpdate) => {
      onAnyUpdate?.(update);
    },
    [onAnyUpdate],
  );

  useWebSocket({
    tournamentId,
    onMatchUpdate: handleMatchUpdate,
  });

  return <>{children}</>;
}
