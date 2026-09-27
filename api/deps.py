"""
api/deps.py — FastAPI Dependency Injection Providers
Provides graph handle, risk cache, database connection, and rate limiter.
"""

import time
from fastapi import Request, Header, HTTPException
import networkx as nx
from typing import Dict, Any

from api.database import get_connection


def get_graph(request: Request) -> nx.MultiDiGraph:
    """Access in-memory NetworkX road graph loaded at startup."""
    return request.app.state.graph


def get_risk_cache(request: Request) -> Dict[int, Dict[str, Any]]:
    """Access live memory-cached segment risks."""
    return request.app.state.risk_cache


def get_db():
    """Yields SQLite database connection with automatic cleanup."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


# In-memory simple rate-limiting tracker (60 requests/minute per device_id)
REQUEST_COUNTS: Dict[str, list] = {}


def verify_device_rate_limit(x_device_id: str = Header(default="dev-driver-guest")):
    """Soft rate limiter: max 60 requests per minute per device ID."""
    now = time.time()
    history = REQUEST_COUNTS.setdefault(x_device_id, [])
    # Filter within last 60 seconds
    REQUEST_COUNTS[x_device_id] = [t for t in history if now - t < 60.0]

    if len(REQUEST_COUNTS[x_device_id]) >= 60:
        raise HTTPException(status_code=429, detail="Device rate limit exceeded (max 60/min)")

    REQUEST_COUNTS[x_device_id].append(now)
    return x_device_id
