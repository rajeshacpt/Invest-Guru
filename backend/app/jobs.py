import time
from typing import Any, Dict

def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    # Simulate long-running task (replace with real provider if you like)
    time.sleep(3)
    # Dummy result; in real life, call your data API here
    return {"ticker": ticker.upper(), "price": 100.25, "status": "ok"}
