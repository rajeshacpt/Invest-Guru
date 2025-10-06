from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from rq import Queue
import redis
import time
from .db import Base, engine
from .models import User, WatchlistItem
from .schemas import RegisterIn, LoginIn, Token, UserOut, WatchlistIn
from .security import hash_password, verify_password, create_access_token
from .core.config import settings
from .deps import get_db, current_user
from .quotes import _fetch_stooq_csv
from .jobs import fetch_stock_data

app = FastAPI(title="Invest-guru API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis Queue
redis_conn = redis.from_url(settings.REDIS_URL)
q = Queue("default", connection=redis_conn)

@app.on_event("startup")
def on_startup():
    # wait for DB (up to ~30s)
    for _ in range(30):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception:
            time.sleep(1)
    Base.metadata.create_all(bind=engine)

@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.ENV}

# --- Auth ---
@app.post("/auth/register", response_model=UserOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(400, "Username already exists")
    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user); db.commit(); db.refresh(user)
    return user

@app.post("/auth/login", response_model=Token)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token(user.username)
    return {"access_token": token}

@app.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user

# --- Watchlist ---
@app.post("/watchlist")
def add_watchlist(item: WatchlistIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    sym = item.symbol.upper()
    db.add(WatchlistItem(user_id=user.id, symbol=sym))
    db.commit()
    return {"ok": True, "symbol": sym}

@app.get("/watchlist")
def list_watchlist(user: User = Depends(current_user), db: Session = Depends(get_db)):
    items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    return [{"id": i.id, "symbol": i.symbol} for i in items]

# --- Quotes ---
@app.get("/quotes/{symbol}")
async def quote(symbol: str):
    try:
        return await _fetch_stooq_csv(symbol)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    '''data = await get_quote_stooq(symbol)
    return data'''

# --- Background jobs ---
@app.post("/jobs/quote")
def enqueue_quote(symbol: str = Body(..., embed=True)):
    job = q.enqueue(fetch_stock_data, symbol)
    return {"job_id": job.get_id()}

@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    from rq.job import Job
    job = Job.fetch(job_id, connection=redis_conn)
    return {
        "id": job.id,
        "status": job.get_status(),
        "result": job.result,
    }
