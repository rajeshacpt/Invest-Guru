import httpx
import yfinance as yf

COMMON_FIXUPS = {
    "APPL": "AAPL",   # common typo
    "GOOGLE": "GOOGL"
}

def _normalize(sym: str) -> list[str]:
    s = sym.strip().upper()
    s = COMMON_FIXUPS.get(s, s)
    # candidates to try (Yahoo works fine with bare symbol; Stooq often wants .us)
    cands = [s]
    if not s.endswith(".US"):
        cands.append(f"{s}.US")   # Yahoo also accepts suffixes
        cands.append(f"{s}.us")   # for Stooq fallback
    return cands

async def _fetch_stooq_csv(symbol: str) -> dict | None:
    url = f"https://stooq.com/q/l/?s={symbol.lower()}&f=sd2t2ohlcvn&h&e=csv"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        lines = [ln.strip() for ln in r.text.splitlines() if ln.strip()]
        if len(lines) < 2:
            return None
        hdrs = [h.strip().lower() for h in lines[0].split(",")]
        vals = [v.strip() for v in lines[1].split(",")]
        row = dict(zip(hdrs, vals))
        if any(row.get(k, "").upper() == "N/D" for k in ("date","time","open","high","low","close")):
            return None
        return {
            "symbol": row.get("symbol", "").upper(),
            "name": row.get("name"),
            "date": row.get("date"),
            "time": row.get("time"),
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "volume": row.get("volume"),
            "source": "stooq",
        }

def _fetch_yahoo(symbol: str) -> dict | None:
    t = yf.Ticker(symbol)
    info = t.fast_info if hasattr(t, "fast_info") else None
    price = None
    if info:
        # fast_info is quick and stable for last price
        price = info.get("last_price")
    if price is None:
        # fallback to .info / .history
        hist = t.history(period="1d", interval="1m")
        if not hist.empty:
            price = float(hist["Close"].iloc[-1])

    # If still nothing, treat as None
    if price is None:
        return None

    # Try to extract some extra fields (best-effort)
    name = None
    try:
        basic = t.get_info() if hasattr(t, "get_info") else t.info  # handles versions
        name = basic.get("shortName") if isinstance(basic, dict) else None
    except Exception:
        pass

    return {
        "symbol": symbol.upper().replace(".US", ""),
        "name": name,
        "date": None,
        "time": None,
        "open": None,
        "high": None,
        "low": None,
        "close": price,
        "volume": None,
        "source": "yfinance",
    }

async def get_quote(symbol: str) -> dict:
    # Try Yahoo first with multiple candidates, then Stooq
    for cand in _normalize(symbol):
        data = _fetch_yahoo(cand)
        if data:
            return data
    for cand in _normalize(symbol):
        data = await _fetch_stooq_csv(cand)
        if data:
            return data
    raise ValueError(f"No quote data found for '{symbol}'. Try a valid ticker like AAPL or MSFT.")



''' import httpx

async def get_quote_stooq(symbol: str) -> dict:
    sym = symbol.lower()
    url = f"https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcvn&h&e=csv"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        lines = [ln.strip() for ln in r.text.splitlines() if ln.strip()]
        if len(lines) < 2:
            raise ValueError("No data")
        headers = [h.strip().lower() for h in lines[0].split(",")]
        values = [v.strip() for v in lines[1].split(",")]
        row = dict(zip(headers, values))
        return {
            "symbol": row.get("symbol", symbol).upper(),
            "name": row.get("name"),
            "date": row.get("date"),
            "time": row.get("time"),
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "volume": row.get("volume"),
        }
        '''


