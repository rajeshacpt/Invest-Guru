# Invest-guru (Auth + Watchlist + Quotes + Redis Jobs) — API on 8100

## Quickstart
```bash
docker compose up --build
```
- Web: http://localhost:3000
- API: http://localhost:8100/health
- Redis: localhost:6379
- Worker: runs automatically

### Flow
1) Register or Login
2) Add ticker (MSFT/AAPL) to watchlist
3) Click **Get Quote** for live price (Stooq)
4) Click **Queue BG Job** to enqueue a background task; poll `/jobs/{job_id}` for result

### Endpoints (new)
- POST `/jobs/quote` body: `{ "symbol": "MSFT" }` → returns `{ job_id }`
- GET `/jobs/{job_id}` → `{ id, status, result }`

### Env
- Backend: `backend/.env` (JWT secret, DB, CORS, REDIS_URL)
- Frontend: `frontend/.env.local` (NEXT_PUBLIC_API_URL)

### Notes
- Passwords hashed (bcrypt); JWT auth for private routes.
- RQ worker processes jobs from Redis.
