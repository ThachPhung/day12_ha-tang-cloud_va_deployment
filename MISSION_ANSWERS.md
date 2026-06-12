# Day 12 Lab - Mission Answers (Part 1–5)

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

1. API key hardcode (`OPENAI_API_KEY = "sk-hardcoded-fake-key..."`)
2. Database password hardcode (`password123` trong `DATABASE_URL`)
3. Không có config management (`DEBUG = True` cố định)
4. Logging bằng `print()` và **log ra secret**
5. Không có `/health` endpoint
6. `host="localhost"`, `port=8000`, `reload=True` — không deploy được lên cloud
7. Không graceful shutdown

### Exercise 1.2: Test basic version

```bash
cd 01-localhost-vs-production/develop
pip3 install -r requirements.txt
python3 app.py
curl -X POST "http://localhost:8000/ask?question=Hello"
```

**Kết quả:**
```json
{"answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé."}
```

**Quan sát:** Chạy được nhưng không production-ready (hardcode, print secret, không health check).

### Exercise 1.3: Comparison table

| Feature | Basic | Advanced | Tại sao quan trọng? |
|---------|-------|----------|---------------------|
| Config | Hardcode | Env vars + `config.py` | Đổi config giữa môi trường không sửa code |
| Health check | Không | `GET /health` | Platform biết khi nào restart |
| Logging | `print()` | JSON structured | Dễ monitor trên cloud |
| Shutdown | Đột ngột | Graceful (lifespan) | Không cắt request đang xử lý |
| Binding | `localhost:8000` | `0.0.0.0` + `PORT` env | Chạy trong container/cloud |
| Secrets | Trong code | `.env` + `.gitignore` | Không lộ khi push Git |

**Test production health:**
```bash
cd 01-localhost-vs-production/production
cp .env.example .env && pip3 install -r requirements.txt
python3 app.py
curl http://localhost:8000/health
```
```json
{"status":"ok","uptime_seconds":1.8,"version":"1.0.0","environment":"development",...}
```

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. **Base image:** `python:3.11`
2. **Working directory:** `/app`
3. **COPY requirements.txt trước:** Layer cache — deps ít đổi, rebuild nhanh khi chỉ sửa code
4. **CMD vs ENTRYPOINT:** CMD override được; ENTRYPOINT là executable cố định

### Exercise 2.2 & 2.3: Build và so sánh image size

```bash
# Từ project root
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .
docker build -f 02-docker/production/Dockerfile -t my-agent:production .
docker images | grep my-agent
```

**Kết quả thực tế:**

| Image | Size |
|-------|------|
| `my-agent:develop` (single-stage) | **1.67 GB** |
| `my-agent:production` (multi-stage slim) | **262 MB** |
| Chênh lệch | **~84% nhỏ hơn** |

### Exercise 2.4: Docker Compose architecture

```
Client → Nginx (:80) → Agent x3 (:8000) → Redis (:6379)
```

- **Stage 1 (builder):** cài gcc + pip dependencies
- **Stage 2 (runtime):** chỉ copy site-packages + code, chạy non-root

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway

App sẵn sàng tại `03-cloud-deployment/railway/`. **Bạn deploy** (cần tài khoản Railway):

```bash
cd 03-cloud-deployment/railway
npm i -g @railway/cli
railway login && railway init
railway variables set AGENT_API_KEY=my-secret-key
railway up && railway domain
```

- **URL:** `[điền sau khi deploy]`
- **Screenshot:** `screenshots/railway-dashboard.png`

### Exercise 3.2: So sánh `render.yaml` vs `railway.toml`

| | Railway | Render |
|--|---------|--------|
| Format | TOML | YAML Blueprint |
| Builder | Nixpacks / Dockerfile | `buildCommand` trong yaml |
| Deploy | `railway up` CLI | Git push + dashboard |
| Health check | `healthcheckPath` | `healthCheckPath` |
| Redis | Add-on riêng | `type: redis` trong blueprint |
| Secrets | `railway variables set` | Dashboard hoặc `envVars` |

---

## Part 4: API Security

### Exercise 4.1: API Key test

```bash
cd 04-api-gateway/develop
AGENT_API_KEY=test-secret-123 python3 app.py
```

| Test | Kết quả |
|------|---------|
| Không có `X-API-Key` | **401** Unauthorized |
| Có key đúng | **200** + JSON answer |

```bash
# 401
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" -d '{"question":"Hello"}'

# 200
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: test-secret-123" \
  -H "Content-Type: application/json" -d '{"question":"Hello"}'
```

### Exercise 4.2: JWT flow

1. `POST /auth/token` → username/password → JWT
2. `POST /ask` với `Authorization: Bearer <token>`
3. `auth.py` decode token → `user_id`, `role`

Demo users: `student/demo123`, `teacher/teach456`

### Exercise 4.3: Rate limiting

- **Algorithm:** Sliding window (deque timestamps)
- **Limit:** 10 req/min (user), 100 req/min (admin)
- **Admin bypass:** `rate_limiter_admin` khi `role == admin`

### Exercise 4.4: Cost guard (Redis)

Đã implement `check_budget()` trong `04-api-gateway/production/cost_guard.py`:

```python
def check_budget(user_id, estimated_cost, monthly_budget_usd=10.0) -> bool:
    key = f"budget:{user_id}:{YYYY-MM}"
    # Redis incrbyfloat + expire 32 days
```

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health & Readiness

```bash
cd 05-scaling-reliability/develop && python3 app.py
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

**Kết quả:**
- `/health` → `{"status":"ok",...}`
- `/ready` → `{"ready":true,"in_flight_requests":0}`

### Exercise 5.2: Graceful shutdown

- `lifespan` chờ in-flight requests (tối đa 30s)
- `SIGTERM` handler log + uvicorn `timeout_graceful_shutdown=30`
- Log khi kill: `🔄 Graceful shutdown initiated...` → `✅ Shutdown complete`

### Exercise 5.3: Stateless design

State lưu Redis (`session:{id}`), không trong memory → scale nhiều instance không mất session.

### Exercise 5.4: Load balancing

```bash
cd 05-scaling-reliability/production
docker compose up --scale agent=3
# Test qua http://localhost:8080
```

### Exercise 5.5: Test stateless

```bash
cd 05-scaling-reliability/production
python3 test_stateless.py
```

---

## Part 6: Final Project — English Flashcard API

### Mô tả

Tích hợp **English Flashcard** vào `06-lab-complete/` kết hợp yêu cầu Day 12:
- Docker multi-stage, Redis, API Key auth, rate limit, cost guard
- Health `/health`, readiness `/ready`, graceful shutdown, JSON logging
- Flashcard API (`/api/*`) + AI tutor `POST /ask` (mock LLM)

### Deploy

- **Platform:** Render
- **URL:** https://day12-ha-tang-cloud-va-deployment-up31.onrender.com
- **Root Directory:** `06-lab-complete`
- **Demo mode:** `DEMO_MODE=true` (không dùng Postgres tạm thời)

### Test kết quả (cloud)

```bash
curl https://day12-ha-tang-cloud-va-deployment-up31.onrender.com/health
# → status: ok, redis: ok, database: skipped, demo_mode: true

curl https://day12-ha-tang-cloud-va-deployment-up31.onrender.com/ready
# → ready: true, redis: true

curl -X POST https://day12-ha-tang-cloud-va-deployment-up31.onrender.com/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
# → 200 + answer JSON
```

### Production readiness

```bash
cd 06-lab-complete && python3 check_production_ready.py
# → 20/20 checks passed
```

Chi tiết deploy: xem `DEPLOYMENT.md`.
