# Deployment Information

> **Bạn điền sau khi deploy.**

## Public URL

```
https://[URL_CỦA_BẠN]
```

## Platform

- [ ] Railway
- [ ] Render

## Environment Variables

| Variable | Value |
|----------|-------|
| `AGENT_API_KEY` | (secret) |
| `REDIS_URL` | (from Redis add-on) |
| `ENVIRONMENT` | `production` |
| `RATE_LIMIT_PER_MINUTE` | `10` |
| `MONTHLY_BUDGET_USD` | `10.0` |

## Test Commands

```bash
curl https://[URL]/health
curl https://[URL]/ready

curl -X POST https://[URL]/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
```
