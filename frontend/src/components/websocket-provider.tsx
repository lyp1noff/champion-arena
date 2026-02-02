"use client";

import React, { createContext, useContext, useMemo } from "react";

import { useWebSocket } from "@/hooks/use-websocket";

interface MatchUpdate {
  match_id: string;
  score_athlete1: number | null;
  score_athlete2: number | null;
  status: string | null;
}

interface WebSocketContextType {
  isConnected: boolean;
  error: string | null;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

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

  const { isConnected, error } = useWebSocket({
    tournamentId,
    onMatchUpdate: handleMatchUpdate,
  });

  const contextValue = useMemo(
    () => ({
      isConnected,
      error,
    }),
    [isConnected, error],
  );

  return <WebSocketContext.Provider value={contextValue}>{children}</WebSocketContext.Provider>;
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocketContext must be used within a WebSocketProvider");
  }
  return context;
}
