## Socket.IO Gateway

- Auth: Expects HS256 JWT signed with `JWT_SECRET` (align with Django `SECRET_KEY`). Client sends it via `auth.token` in the Socket.IO handshake.
- Redis: Uses `REDIS_URL` for pub/sub adapter so multiple instances stay in sync.
- Events:
  - `join_session` `{ sessionId }`
  - `leave_session` `{ sessionId }`
  - `code_update` `{ sessionId, code, language }` (broadcast to room except sender)
  - `chat_message` `{ sessionId, message }`
  - `typing` `{ sessionId, isTyping }`
- Responses: mirrors events back to the room; includes `from` and `at` on broadcasts.

### Run locally
```bash
cd realtime-server
cp ../.env.sample ../.env # adjust SOCKET_* and JWT_SECRET to match Django
npm install
npm run dev
```

Env vars:
- `SOCKET_PORT` (default 4000)
- `SOCKET_CORS_ORIGINS` (comma-separated origins, e.g. `http://localhost:5174`)
- `JWT_SECRET` (same as Django SECRET_KEY)
- `REDIS_URL` (e.g. `redis://127.0.0.1:6379/0`)
