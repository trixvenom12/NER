"""
api/main.py — FastAPI Application Entry Point
Lifespan loader: initializes DB, loads road graph, loads ML model,
populates risk cache from segment_risk table, mounts static frontend.
"""

import os
import json
from contextlib import asynccontextmanager

import networkx as nx
import joblib
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.database import init_db, get_connection

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _load_risk_cache() -> dict:
    """Load pre-computed segment risks from DB into memory dict."""
    cache = {}
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Get the latest risk for each segment
        cur.execute("""
            SELECT sr.segment_id, sr.score, sr.band, sr.factors
            FROM segment_risk sr
            INNER JOIN (
                SELECT segment_id, MAX(computed_at) AS latest
                FROM segment_risk GROUP BY segment_id
            ) latest_sr
            ON sr.segment_id = latest_sr.segment_id
            AND sr.computed_at = latest_sr.latest;
        """)
        for row in cur.fetchall():
            factors = row["factors"]
            if isinstance(factors, str):
                factors = json.loads(factors)
            cache[row["segment_id"]] = {
                "score": row["score"],
                "band": row["band"],
                "factors": factors,
            }
        conn.close()
        print(f"[OK] Loaded risk cache: {len(cache)} segments")
    except Exception as e:
        print(f"[WARN] Could not load risk cache: {e}")
    return cache


def ensure_initialized(app: FastAPI):
    """
    Idempotent initializer for database, road graph, ML model, and risk cache.
    Works for both traditional persistent servers and serverless cold starts.
    """
    # 1. Initialize database tables
    init_db()

    # 2. Load road graph if not already loaded
    if not hasattr(app.state, "graph") or app.state.graph is None:
        graph_candidates = [
            os.path.join(os.path.dirname(__file__), "graph", "ner_drive.graphml"),
            os.path.join(_PROJECT_ROOT, "data", "graph", "ner_drive.graphml"),
        ]
        graph_path = next((p for p in graph_candidates if os.path.exists(p)), None)
        if graph_path:
            try:
                app.state.graph = nx.read_graphml(graph_path)
                print(f"[OK] Road graph loaded: {app.state.graph.number_of_nodes()} nodes, "
                      f"{app.state.graph.number_of_edges()} edges")
            except Exception as e:
                print(f"[WARN] Failed to load graph: {e}")
                app.state.graph = None
        else:
            print(f"[WARN] Graph file not found. Candidates: {graph_candidates}")
            app.state.graph = None

    # 3. Load ML risk model if not already loaded
    if not hasattr(app.state, "model") or app.state.model is None:
        model_candidates = [
            os.path.join(os.path.dirname(__file__), "models_data", "risk_model.joblib"),
            os.path.join(_PROJECT_ROOT, "models", "risk_model.joblib"),
        ]
        model_path = next((p for p in model_candidates if os.path.exists(p)), None)
        if model_path:
            try:
                app.state.model = joblib.load(model_path)
                print(f"[OK] ML risk model loaded from {model_path}")
            except Exception as e:
                print(f"[WARN] Failed to load ML model: {e}")
                app.state.model = None
        else:
            app.state.model = None

    # 4. Populate risk cache from segment_risk table
    if not hasattr(app.state, "risk_cache") or not app.state.risk_cache:
        app.state.risk_cache = _load_risk_cache()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown lifespan event handler."""
    ensure_initialized(app)
    yield


app = FastAPI(
    title="NER Logistics Intelligence",
    description="AI-Based Smart Logistics Platform for NH-6 Corridor",
    version="1.0.0",
    lifespan=lifespan,
)

# Eagerly initialize state for serverless environments (Vercel)
try:
    ensure_initialized(app)
except Exception as e:
    print(f"[WARN] Startup eager initialization notice: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    )



# ─── Register ALL routers ───────────────────────────────────────────
from api.routers.routes import router as routes_router
from api.routers.risk import router as risk_router
from api.routers.facilities import router as facilities_router
from api.routers.reports import router as reports_router
from api.routers.analytics import router as analytics_router
from api.routers.sync import router as sync_router
from api.routers.precursor import router as precursor_router

# routes_router has prefix="/api" set inside the file
app.include_router(routes_router)
# These routers already have their own /api/* prefixes
app.include_router(risk_router)
app.include_router(facilities_router)
app.include_router(reports_router)
app.include_router(analytics_router)
app.include_router(sync_router)
app.include_router(precursor_router)


@app.get("/api/health", tags=["Health"])
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "NER Logistics Intelligence API",
        "version": "1.0.0",
    }


@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "NER Logistics Intelligence API",
        "docs": "/docs",
        "version": "1.0.0",
    }
