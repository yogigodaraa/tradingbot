"use client";

import { useEffect, useRef, useState, useCallback } from "react";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws/live";

interface WSMessage {
  type: string;
  [key: string]: unknown;
}

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    // Set on unmount so a socket closing during cleanup doesn't schedule a reconnect.
    let disposed = false;

    const connect = () => {
      if (disposed) return;
      try {
        const socket = new WebSocket(WS_URL);
        ws.current = socket;

        socket.onopen = () => {
          setConnected(true);
          console.log("WebSocket connected");
        };

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setLastMessage(data);
          } catch {
            console.error("Failed to parse WS message");
          }
        };

        socket.onclose = () => {
          setConnected(false);
          // Auto-reconnect after 3 seconds
          if (!disposed) reconnectTimeout.current = setTimeout(connect, 3000);
        };

        socket.onerror = () => {
          socket.close();
        };
      } catch {
        if (!disposed) reconnectTimeout.current = setTimeout(connect, 3000);
      }
    };

    connect();
    return () => {
      disposed = true;
      clearTimeout(reconnectTimeout.current);
      ws.current?.close();
    };
  }, []);

  const sendMessage = useCallback((data: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(data);
    }
  }, []);

  return { connected, lastMessage, sendMessage };
}
