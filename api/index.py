"""
api/index.py — Vercel Serverless Function Entrypoint
Exposes the FastAPI 'app' instance for Vercel's Python Serverless Runtime.
"""

import os
import sys

# Ensure both project root and api directory are available on sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, ".."))

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from api.main import app as fastapi_app, ensure_initialized

# Ensure in-memory graph, database, and models are loaded for serverless cold start
try:
    ensure_initialized(fastapi_app)
except Exception as e:
    print(f"[WARN] Cold start initialization warning: {e}")


class VercelPathFixMiddleware:
    """Raw ASGI middleware to fix Vercel rewrite paths before Starlette routing."""
    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            matched = (
                headers.get(b"x-matched-path")
                or headers.get(b"x-forwarded-uri")
                or headers.get(b"x-original-uri")
            )
            if matched:
                try:
                    path_str = matched.decode("utf-8").split("?")[0]
                    if path_str:
                        scope["path"] = path_str
                except Exception:
                    pass
        await self.inner_app(scope, receive, send)


app = VercelPathFixMiddleware(fastapi_app)
