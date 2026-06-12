# Deployment Information — English Flashcard API (Day 12 Part 6)

## Public URL

```
https://day12-ha-tang-cloud-va-deployment-up31.onrender.com
```

## Platform

- [x] Render

## Environment Variables (Render Dashboard)

| Variable | Value | Ghi chú |
|----------|--------|---------|
| `AGENT_API_KEY` | (secret) | API key cho `POST /ask` |
| `REDIS_URL` | `redis://red-d8ltf5kvikkc73bsq9dg:6379` | Render Key Value |
| `ENVIRONMENT` | `production` | |
| `DEMO_MODE` | `true` | Chạy demo không cần Postgres |
| `RATE_LIMIT_PER_MINUTE` | `10` | |
| `MONTHLY_BUDGET_USD` | `10.0` | |
| `SECRET_KEY` | (secret) | JWT flashcard |
| `CORS_ORIGINS` | `*` | |
| `LOG_LEVEL` | `info` | |
| `DATABASE_URL` | — | **Đã xóa** (demo mode) |

> Sau này bật Flashcard đầy đủ: thêm `DATABASE_URL` (Supabase), đặt `DEMO_MODE=false`.

## Test Commands

### Health

```bash
curl https://day12-ha-tang-cloud-va-deployment-up31.onrender.com/health
```

**Kết quả thực tế:**
```json
{"status":"ok","demo_mode":true,"database":"skipped","redis":"ok",...}
```

### Ready

```bash
curl https://day12-ha-tang-cloud-va-deployment-up31.onrender.com/ready
```

**Kết quả thực tế:**
```json
{"ready":true,"redis":true,"database":false,"demo_mode":true}
```

### AI English tutor — `POST /ask` (Day 12)

```bash
curl -X POST https://day12-ha-tang-cloud-va-deployment-up31.onrender.com/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
```

**Kết quả:** `200` — JSON có `"answer":"..."`

### Auth required (không có key)

```bash
curl -X POST https://day12-ha-tang-cloud-va-deployment-up31.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
```

**Kết quả:** `401 Unauthorized`

## Expected Results

| Endpoint | Status | Ghi chú |
|----------|--------|---------|
| `GET /health` | `200` | `redis: ok`, `database: skipped` (demo) |
| `GET /ready` | `200` | `ready: true` |
| `POST /ask` (no key) | `401` | |
| `POST /ask` (with key) | `200` | Mock LLM English answer |
| `POST /api/auth/login` | — | Chưa dùng (cần DB khi tắt demo mode) |

## Screenshots

- [x] `06-lab-complete/results.png` — kết quả test deploy
- [x] Render Dashboard — service **Live**
- [x] Environment variables (đã cấu hình `DEMO_MODE=true`)

## Self-Test Checklist

- [x] Deploy thành công trên Render
- [x] Public URL hoạt động
- [x] `/health` trả `200`
- [x] `/ready` trả `200`
- [x] `/ask` yêu cầu API key (`401` không key)
- [x] `/ask` với key trả `200`
- [x] Redis kết nối OK
- [x] `python3 check_production_ready.py` → 20/20 (local)
