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

from api.main import app, ensure_initialized

# Ensure in-memory graph, database, and models are loaded for serverless cold start
ensure_initialized(app)
