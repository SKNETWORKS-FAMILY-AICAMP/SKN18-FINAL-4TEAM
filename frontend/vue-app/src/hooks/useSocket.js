import { io } from "socket.io-client";
import { onBeforeUnmount, ref } from "vue";

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || "http://localhost:4000";

/**
 * Lightweight Socket.IO helper.
 * Call connect(token, sessionId) after login, then use emit helpers.
 */
export function useSocket() {
  const socket = ref(null);
  const isConnected = ref(false);
  const lastError = ref("");

  const connect = (token, sessionId) => {
    if (!token) {
      lastError.value = "missing token";
      return;
    }
    if (socket.value) {
      socket.value.disconnect();
    }

    const instance = io(SOCKET_URL, {
      transports: ["websocket"],
      auth: { token },
      autoConnect: true,
    });
    socket.value = instance;
    lastError.value = "";

    instance.on("connect", () => {
      isConnected.value = true;
      if (sessionId) {
        instance.emit("join_session", { sessionId });
      }
    });

    instance.on("disconnect", () => {
      isConnected.value = false;
    });

    instance.on("connect_error", (err) => {
      lastError.value = err?.message || "connect_error";
      isConnected.value = false;
    });
  };

  const disconnect = () => {
    if (socket.value) {
      socket.value.disconnect();
      socket.value = null;
      isConnected.value = false;
    }
  };

  const joinSession = (sessionId) => {
    if (socket.value && sessionId) { 
      socket.value.emit("join_session", { sessionId });
    }
  };

  const leaveSession = (sessionId) => {
    if (socket.value) {
      socket.value.emit("leave_session", { sessionId });
    }
  };

  const emitCodeUpdate = (sessionId, code, language) => {
    if (socket.value && sessionId) {
      socket.value.emit("code_update", { sessionId, code, language });
    }
  };

  const emitChatMessage = (sessionId, message) => {
    if (socket.value && sessionId && message) {
      socket.value.emit("chat_message", { sessionId, message });
    }
  };

  const onEvent = (event, handler) => {
    if (!socket.value || !event || typeof handler !== "function") return;
    socket.value.on(event, handler);
    return () => socket.value?.off(event, handler);
  };

  onBeforeUnmount(() => {
    disconnect();
  });

  return {
    socket,
    isConnected,
    lastError,
    connect,
    disconnect,
    joinSession,
    leaveSession,
    emitCodeUpdate,
    emitChatMessage,
    onEvent,
  };
}
