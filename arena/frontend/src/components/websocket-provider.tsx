"use client";

import React from "react";

import { useWebSocket } from "@/hooks/use-websocket";

interface WebSocketProviderProps {
  children: React.ReactNode;
  tournamentId: string;
  /** Called with the ids of brackets that changed on the server. */
  onBracketsUpdated?: (bracketIds: number[]) => void;
}

export function WebSocketProvider({ children, tournamentId, onBracketsUpdated }: WebSocketProviderProps) {
  useWebSocket({ tournamentId, onBracketsUpdated: (ids) => onBracketsUpdated?.(ids) });
  return <>{children}</>;
}
