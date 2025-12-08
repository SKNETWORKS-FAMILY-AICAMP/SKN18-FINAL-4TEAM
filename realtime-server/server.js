require("dotenv").config();
const http = require("http");
const jwt = require("jsonwebtoken");
const { Server } = require("socket.io");
const { createClient } = require("redis");
const { createAdapter } = require("@socket.io/redis-adapter");

const PORT = process.env.SOCKET_PORT ? Number(process.env.SOCKET_PORT) : 4000;
const JWT_SECRET = process.env.JWT_SECRET || process.env.SECRET_KEY || "development-secret-key";
const REDIS_URL = process.env.REDIS_URL || "redis://127.0.0.1:6379/0";
const CORS_ORIGINS = (process.env.SOCKET_CORS_ORIGINS || "").split(",").filter(Boolean);

const server = http.createServer();
const io = new Server(server, {
  cors: {
    origin: CORS_ORIGINS.length ? CORS_ORIGINS : "*",
    credentials: true,
  },
});

async function initRedisAdapter() {
  const pubClient = createClient({ url: REDIS_URL });
  const subClient = pubClient.duplicate();
  await Promise.all([pubClient.connect(), subClient.connect()]);
  io.adapter(createAdapter(pubClient, subClient));
  return { pubClient, subClient };
}

function authenticateSocket(socket, next) {
  const token =
    socket.handshake.auth?.token ||
    socket.handshake.headers?.authorization?.split(" ")[1] ||
    socket.handshake.query?.token;

  if (!token) {
    return next(new Error("unauthorized: missing token"));
  }

  try {
    const payload = jwt.verify(token, JWT_SECRET);
    socket.user = { id: payload.sub, email: payload.email };
    return next();
  } catch (err) {
    return next(new Error("unauthorized: invalid token"));
  }
}

function registerHandlers() {
  io.use(authenticateSocket);

  io.on("connection", (socket) => {
    const userId = socket.user?.id;
    if (!userId) {
      socket.disconnect(true);
      return;
    }

    socket.join(`user:${userId}`);

    socket.on("join_session", async ({ sessionId }) => {
      if (!sessionId) return;
      socket.join(`session:${sessionId}`);
      socket.data.sessionId = sessionId;
      socket.emit("session_joined", { sessionId });
    });

    socket.on("leave_session", ({ sessionId }) => {
      const target = sessionId || socket.data.sessionId;
      if (!target) return;
      socket.leave(`session:${target}`);
      socket.emit("session_left", { sessionId: target });
      if (socket.data.sessionId === target) {
        socket.data.sessionId = undefined;
      }
    });

    socket.on("code_update", ({ sessionId, code, language }) => {
      const target = sessionId || socket.data.sessionId;
      if (!target || typeof code !== "string") return;
      socket.to(`session:${target}`).emit("code_update", {
        sessionId: target,
        code,
        language: language || null,
        from: userId,
        at: Date.now(),
      });
    });

    socket.on("chat_message", ({ sessionId, message }) => {
      const target = sessionId || socket.data.sessionId;
      if (!target || typeof message !== "string" || !message.trim()) return;
      io.to(`session:${target}`).emit("chat_message", {
        sessionId: target,
        from: userId,
        message: message.trim(),
        at: Date.now(),
      });
    });

    socket.on("typing", ({ sessionId, isTyping }) => {
      const target = sessionId || socket.data.sessionId;
      if (!target) return;
      socket.to(`session:${target}`).emit("typing", {
        sessionId: target,
        from: userId,
        isTyping: !!isTyping,
      });
    });

    socket.on("disconnect", () => {
      if (socket.data?.sessionId) {
        socket.leave(`session:${socket.data.sessionId}`);
      }
    });
  });
}

async function main() {
  try {
    await initRedisAdapter();
    registerHandlers();
    server.listen(PORT, () => {
      /* eslint-disable no-console */
      console.log(`Socket.IO gateway listening on :${PORT}`);
    });
  } catch (err) {
    console.error("Failed to start Socket.IO gateway", err);
    process.exit(1);
  }
}

main();
