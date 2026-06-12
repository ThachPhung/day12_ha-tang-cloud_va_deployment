# Part 6 — English Flashcard API (Production)

Kết hợp **English Flashcard** + yêu cầu **Day 12** (Docker, Redis, auth, rate limit, health checks).

## Tính năng

**Flashcard API** (`/api/*`):
- Đăng nhập JWT: `POST /api/auth/login`
- Bộ từ, thẻ, học SRS: `/api/decks`, `/api/study`, ...
- Admin mặc định: `admin` / `admin1234`

**Day 12 production**:
- `GET /health`, `GET /ready`
- `POST /ask` — AI English tutor (mock LLM, cần `X-API-Key`)
- Rate limit + cost guard (Redis)

## Chạy local

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8080
- Docs: http://localhost:8080/docs

```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin1234"}'
curl -X POST http://localhost:8080/ask \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"How to learn vocabulary?"}'
```

## Kiểm tra

```bash
python3 check_production_ready.py
```

## Deploy Render

Xem `render.yaml`. Cần set `DATABASE_URL` (Supabase/Postgres) trên Dashboard.
