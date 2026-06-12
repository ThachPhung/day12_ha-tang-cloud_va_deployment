# Lab 12 — Part 6: Production AI Agent

## Chạy local

```bash
cp .env.example .env
docker compose up --build
```

Test:

```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/ask \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"What is deployment?"}'
```

## Kiểm tra

```bash
python3 check_production_ready.py
```

## Deploy (bạn tự làm)

### Railway

```bash
npm i -g @railway/cli
railway login
railway init
railway add redis
railway variables set AGENT_API_KEY=your-secret-key
railway variables set ENVIRONMENT=production
railway up
railway domain
```

### Render

Push GitHub → Render Dashboard → New Blueprint → connect repo → set secrets → Deploy.

Điền URL vào `DEPLOYMENT.md` sau khi deploy xong.
