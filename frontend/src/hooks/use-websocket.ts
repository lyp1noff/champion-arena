import { useCallback, useEffect, useRef, useState } from "react";

import { BACKEND_URL } from "@/lib/config";

interface MatchUpdate {
  match_id: string;
  score_athlete1: number | null;
  score_athlete2: number | null;
  status: string | null;
}

interface UseWebSocketOptions {
  tournamentId: string;
  onMatchUpdate?: (update: MatchUpdate) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export function useWebSocket({ tournamentId, onMatchUpdate, onConnect, onDisconnect, onError }: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = BACKEND_URL.replace(/^http/, "ws") + `/ws/tournament/${tournamentId}`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Check if it's a match update
          if (data.match_id && (data.score_athlete1 !== undefined || data.score_athlete2 !== undefined)) {
            onMatchUpdate?.(data as MatchUpdate);
          }
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        onDisconnect?.();

        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current - 1), 30000);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setError("Failed to reconnect after maximum attempts");
        }
      };

      ws.onerror = (event) => {
        setError("WebSocket connection error");
        onError?.(event);
      };
    } catch (err) {
      setError("Failed to create WebSocket connection");
      console.error("WebSocket connection error:", err);
    }
  }, [tournamentId, onMatchUpdate, onConnect, onDisconnect, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, "Manual disconnect");
      wsRef.current = null;
    }

    setIsConnected(false);
    reconnectAttempts.current = 0;
  }, []);

  const sendMessage = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    error,
    sendMessage,
    connect,
    disconnect,
  };
}
