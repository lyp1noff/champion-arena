import { useCallback, useEffect, useRef, useState } from "react";

import { BACKEND_URL } from "@/lib/config";
import { BRACKET_STATUS, Bracket, BracketMatches } from "@/lib/interfaces";

/** Lightweight notice for brackets this connection is not subscribed to. */
export interface BracketHeaderUpdate {
  id: number;
  status: BRACKET_STATUS;
  version: number;
}

/** Full current state of a bracket this connection is subscribed to. */
export interface BracketStateUpdate {
  bracket: Bracket;
  matches: BracketMatches;
}

interface UseWebSocketOptions {
  tournamentId: string;
  /** Brackets to receive full state for (the ones on screen). Others only get headers. */
  subscribedBracketIds?: number[];
  /** Called with the ids of brackets that changed (and, from newer servers, their status/version). */
  onBracketsUpdated?: (bracketIds: number[], headers: BracketHeaderUpdate[]) => void;
  onBracketState?: (update: BracketStateUpdate) => void;
  /** Called after a dropped connection is re-established: updates may have been missed. */
  onReconnect?: () => void;
}

const MAX_RECONNECT_DELAY_MS = 30_000;

function buildWebSocketUrl(baseUrl: string, tournamentId: string): string {
  const suffix = `/ws/tournament/${tournamentId}`;
  const trimmed = baseUrl.replace(/\/+$/, "");

  if (trimmed.startsWith("ws://") || trimmed.startsWith("wss://")) {
    return `${trimmed}${suffix}`;
  }

  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
    return `${trimmed.replace(/^http/, "ws")}${suffix}`;
  }

  if (typeof window !== "undefined") {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    if (trimmed.startsWith("/")) {
      return `${wsProtocol}//${window.location.host}${trimmed}${suffix}`;
    }
    return `${wsProtocol}//${trimmed}${suffix}`;
  }

  return `${trimmed}${suffix}`;
}

/**
 * One tournament WebSocket. Reconnects forever with capped backoff (and immediately when the
 * tab becomes visible or the network comes back), re-sending the subscription each time.
 * Callbacks are read through refs, so callers don't need to memoize them.
 */
export function useWebSocket({
  tournamentId,
  subscribedBracketIds,
  onBracketsUpdated,
  onBracketState,
  onReconnect,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);

  const handlersRef = useRef({ onBracketsUpdated, onBracketState, onReconnect });
  handlersRef.current = { onBracketsUpdated, onBracketState, onReconnect };

  const subscriptionKey = subscribedBracketIds ? [...subscribedBracketIds].sort((a, b) => a - b).join(",") : null;
  const subscriptionRef = useRef<string | null>(subscriptionKey);
  const wsRef = useRef<WebSocket | null>(null);

  const sendSubscription = useCallback(() => {
    const ws = wsRef.current;
    const key = subscriptionRef.current;
    if (key === null || !ws || ws.readyState !== WebSocket.OPEN) return;
    const ids = key ? key.split(",").map(Number) : [];
    ws.send(JSON.stringify({ type: "subscribe", bracket_ids: ids }));
  }, []);

  useEffect(() => {
    subscriptionRef.current = subscriptionKey;
    sendSubscription();
  }, [subscriptionKey, sendSubscription]);

  useEffect(() => {
    if (!tournamentId || tournamentId === "undefined") return;

    let disposed = false;
    let attempts = 0;
    let everConnected = false;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    const scheduleReconnect = () => {
      if (disposed || retryTimer) return;
      const base = Math.min(1000 * 2 ** attempts, MAX_RECONNECT_DELAY_MS);
      attempts += 1;
      retryTimer = setTimeout(
        () => {
          retryTimer = null;
          connect();
        },
        base / 2 + Math.random() * (base / 2),
      );
    };

    const connect = () => {
      if (disposed) return;
      const current = wsRef.current;
      if (current && (current.readyState === WebSocket.OPEN || current.readyState === WebSocket.CONNECTING)) return;

      let ws: WebSocket;
      try {
        ws = new WebSocket(buildWebSocketUrl(BACKEND_URL, tournamentId));
      } catch (err) {
        console.error("WebSocket connection error:", err);
        scheduleReconnect();
        return;
      }
      wsRef.current = ws;

      ws.onopen = () => {
        attempts = 0;
        setIsConnected(true);
        sendSubscription();
        if (everConnected) handlersRef.current.onReconnect?.();
        everConnected = true;
      };

      ws.onmessage = (event) => {
        let data: unknown;
        try {
          data = JSON.parse(event.data);
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
          return;
        }
        if (!data || typeof data !== "object") return;
        const message = data as Record<string, unknown>;
        if (message.type === "bracket_state" && message.bracket && Array.isArray(message.matches)) {
          handlersRef.current.onBracketState?.({
            bracket: message.bracket as Bracket,
            matches: message.matches as BracketMatches,
          });
        } else if (message.type === "brackets_updated" && Array.isArray(message.bracket_ids)) {
          const headers = Array.isArray(message.brackets) ? (message.brackets as BracketHeaderUpdate[]) : [];
          handlersRef.current.onBracketsUpdated?.(message.bracket_ids.map(Number), headers);
        }
      };

      ws.onclose = () => {
        if (wsRef.current === ws) wsRef.current = null;
        setIsConnected(false);
        scheduleReconnect();
      };

      ws.onerror = () => {
        // onclose follows and handles the retry.
      };
    };

    const reconnectNow = () => {
      if (disposed) return;
      if (retryTimer) {
        clearTimeout(retryTimer);
        retryTimer = null;
      }
      attempts = 0;
      connect();
    };

    const onVisibility = () => {
      if (document.visibilityState === "visible") reconnectNow();
    };

    connect();
    window.addEventListener("online", reconnectNow);
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      disposed = true;
      window.removeEventListener("online", reconnectNow);
      document.removeEventListener("visibilitychange", onVisibility);
      if (retryTimer) clearTimeout(retryTimer);
      const ws = wsRef.current;
      wsRef.current = null;
      if (ws) {
        ws.onclose = null;
        ws.close(1000, "Manual disconnect");
      }
      setIsConnected(false);
    };
  }, [tournamentId, sendSubscription]);

  return { isConnected };
}
