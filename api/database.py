"""
api/database.py — SQLite Database Connection & Initialization
Provides raw sqlite3 connections with Row factory for dict-like access.
All routers and services depend on get_connection() and init_db().
"""

import os
import shutil
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Resolve DB and schema paths relative to project root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ORIGINAL_DB = os.path.join(_PROJECT_ROOT, "data", "ner_logistics.db")
SCHEMA_PATH = os.path.join(_PROJECT_ROOT, "data", "schema.sql")

# In serverless environments (Vercel, AWS Lambda), copy DB to /tmp for write access
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    TMP_DB = os.path.join("/tmp", "ner_logistics.db")
    if os.path.exists(_ORIGINAL_DB) and not os.path.exists(TMP_DB):
        try:
            shutil.copy2(_ORIGINAL_DB, TMP_DB)
        except Exception as e:
            print(f"[WARN] Failed to copy SQLite DB to /tmp: {e}")
    DB_PATH = TMP_DB if os.path.exists(TMP_DB) else _ORIGINAL_DB
else:
    DB_PATH = _ORIGINAL_DB

DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_connection() -> sqlite3.Connection:
    """
    Returns a new sqlite3 connection with Row factory enabled.
    Callers are responsible for closing the connection.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    try:
        conn.execute("PRAGMA foreign_keys=ON;")
    except Exception:
        pass
    return conn


def init_db():
    """
    Executes the DDL schema to create all 6 tables if they don't exist.
    Safe to call multiple times (uses CREATE TABLE IF NOT EXISTS).
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if not os.path.exists(SCHEMA_PATH):
        print(f"[WARN] Schema file not found at {SCHEMA_PATH}. Skipping init_db.")
        return

    conn = get_connection()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.close()
    print(f"[OK] Database initialized at {DB_PATH}")
