"use client";

import React, { createContext, useCallback, useContext, useMemo } from "react";

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
  matchUpdates: Map<string, MatchUpdate>;
  subscribeToMatch: (matchId: string, callback: (update: MatchUpdate) => void) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: React.ReactNode;
  tournamentId: string;
}

export function WebSocketProvider({ children, tournamentId }: WebSocketProviderProps) {
  const [matchUpdates, setMatchUpdates] = React.useState<Map<string, MatchUpdate>>(new Map());
  const [subscribers, setSubscribers] = React.useState<Map<string, Set<(update: MatchUpdate) => void>>>(new Map());

  const handleMatchUpdate = useCallback(
    (update: MatchUpdate) => {
      setMatchUpdates((prev) => {
        const newMap = new Map(prev);
        newMap.set(update.match_id, update);
        return newMap;
      });

      const matchSubscribers = subscribers.get(update.match_id);
      if (matchSubscribers) {
        matchSubscribers.forEach((callback) => callback(update));
      }
    },
    [subscribers],
  );

  const { isConnected, error } = useWebSocket({
    tournamentId,
    onMatchUpdate: handleMatchUpdate,
  });

  const subscribeToMatch = useCallback((matchId: string, callback: (update: MatchUpdate) => void) => {
    setSubscribers((prev) => {
      const newSubscribers = new Map(prev);
      if (!newSubscribers.has(matchId)) {
        newSubscribers.set(matchId, new Set());
      }
      newSubscribers.get(matchId)!.add(callback);
      return newSubscribers;
    });

    return () => {
      setSubscribers((prev) => {
        const newSubscribers = new Map(prev);
        const matchSubscribers = newSubscribers.get(matchId);
        if (matchSubscribers) {
          matchSubscribers.delete(callback);
          if (matchSubscribers.size === 0) {
            newSubscribers.delete(matchId);
          }
        }
        return newSubscribers;
      });
    };
  }, []);

  const contextValue = useMemo(
    () => ({
      isConnected,
      error,
      matchUpdates,
      subscribeToMatch,
    }),
    [isConnected, error, matchUpdates, subscribeToMatch],
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

export function useMatchUpdate(matchId: string) {
  const { subscribeToMatch, matchUpdates } = useWebSocketContext();
  const [update, setUpdate] = React.useState<MatchUpdate | null>(matchUpdates.get(matchId) || null);

  React.useEffect(() => {
    const unsubscribe = subscribeToMatch(matchId, (newUpdate) => {
      setUpdate(newUpdate);
    });

    return unsubscribe;
  }, [matchId, subscribeToMatch]);

  return update;
}
