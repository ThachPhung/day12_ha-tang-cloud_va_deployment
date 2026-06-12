# Deployment Information — English Flashcard API

## Public URL

```
https://day12-ha-tang-cloud-va-deployment-up31.onrender.com
```

## Platform

- [x] Render

## Environment Variables

| Variable | Value |
|----------|-------|
| `AGENT_API_KEY` | (secret — Render Dashboard) |
| `REDIS_URL` | `redis://red-d8ltf5kvikkc73bsq9dg:6379` |
| `DATABASE_URL` | (PostgreSQL / Supabase — set on Dashboard) |
| `SECRET_KEY` | (JWT secret — auto or manual) |
| `ENVIRONMENT` | `production` |
| `RATE_LIMIT_PER_MINUTE` | `10` |
| `MONTHLY_BUDGET_USD` | `10.0` |
| `CORS_ORIGINS` | `*` |

## Test Commands

### Health & Ready

```bash
curl https://day12-ha-tang-cloud-va-deployment-up31.onrender.com/health
curl https://day12-ha-tang-cloud-va-deployment-up31.onrender.com/ready
```

### Flashcard login

```bash
curl -X POST https://day12-ha-tang-cloud-va-deployment-up31.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin1234"}'
```

### AI English tutor (Day 12 /ask)

```bash
curl -X POST https://day12-ha-tang-cloud-va-deployment-up31.onrender.com/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"How to remember English words?"}'
```

## Expected Results

| Endpoint | Expected |
|----------|----------|
| `GET /health` | `200` — database + redis ok |
| `GET /ready` | `200` — `{"ready":true,...}` |
| `POST /api/auth/login` | `200` — JWT token |
| `POST /ask` (no key) | `401` |
| `POST /ask` (with key) | `200` — English answer |

## Screenshots

- [ ] `screenshots/dashboard.png`
- [ ] `screenshots/running.png`
- [ ] `screenshots/test.png`
