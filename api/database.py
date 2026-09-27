"""
api/database.py — Dual-Mode Database Connection & Initialization
Supports Supabase (PostgreSQL via DATABASE_URL or SUPABASE_DB_URL)
and local SQLite (ner_logistics.db) with seamless dict-like access.
"""

import os
import shutil
import sqlite3
from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Resolve DB and schema paths relative to project root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ORIGINAL_DB = os.path.join(_PROJECT_ROOT, "data", "ner_logistics.db")
SQLITE_SCHEMA_PATH = os.path.join(_PROJECT_ROOT, "data", "schema.sql")
SUPABASE_SCHEMA_PATH = os.path.join(_PROJECT_ROOT, "data", "supabase_schema.sql")

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
except Exception:
    pass

# Read database URL from environment
RAW_DB_URL = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL") or ""
IS_POSTGRES = RAW_DB_URL.startswith("postgres://") or RAW_DB_URL.startswith("postgresql://")

if IS_POSTGRES:
    # Normalize postgres:// to postgresql:// for SQLAlchemy
    DATABASE_URL = RAW_DB_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    DB_PATH = DATABASE_URL
else:
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


class PostgresCursorWrapper:
    """Adapts psycopg2 cursor to mirror sqlite3 cursor semantics (dict access & '?' params)."""
    def __init__(self, raw_cur: Any):
        self._cur = raw_cur

    def execute(self, query: str, params: Any = None):
        if params is not None and "?" in query:
            query = query.replace("?", "%s")
        if params is not None:
            return self._cur.execute(query, params)
        return self._cur.execute(query)

    def executemany(self, query: str, seq_of_params: Any):
        if "?" in query:
            query = query.replace("?", "%s")
        return self._cur.executemany(query, seq_of_params)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def fetchmany(self, size: int = 1):
        return self._cur.fetchmany(size)

    @property
    def rowcount(self):
        return self._cur.rowcount

    def close(self):
        return self._cur.close()

    def __iter__(self):
        return iter(self._cur)


class PostgresConnectionWrapper:
    """Wraps psycopg2 connection to mirror sqlite3 Connection interface."""
    def __init__(self, raw_conn: Any):
        self._conn = raw_conn

    def cursor(self):
        from psycopg2.extras import RealDictCursor
        return PostgresCursorWrapper(self._conn.cursor(cursor_factory=RealDictCursor))

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def execute(self, query: str, params: Any = None):
        cur = self.cursor()
        cur.execute(query, params)
        return cur


def get_connection():
    """
    Returns a database connection with dict-like row access.
    Automatically connects to Supabase PostgreSQL when DATABASE_URL is set,
    otherwise falls back cleanly to SQLite.
    """
    if IS_POSTGRES:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        raw = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return PostgresConnectionWrapper(raw)

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
    Initializes database tables if they do not exist.
    Executes PostgreSQL DDL for Supabase or SQLite DDL for local SQLite.
    Safe to call multiple times (uses CREATE TABLE IF NOT EXISTS).
    """
    if IS_POSTGRES:
        if not os.path.exists(SUPABASE_SCHEMA_PATH):
            print(f"[WARN] Supabase schema file not found at {SUPABASE_SCHEMA_PATH}.")
            return
        conn = get_connection()
        try:
            with open(SUPABASE_SCHEMA_PATH, "r") as f:
                conn.execute(f.read())
            conn.commit()
            print("[OK] Supabase PostgreSQL database initialized.")
        except Exception as e:
            conn.rollback()
            print(f"[WARN] Supabase init_db notice: {e}")
        finally:
            conn.close()
        return

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(SQLITE_SCHEMA_PATH):
        print(f"[WARN] Schema file not found at {SQLITE_SCHEMA_PATH}. Skipping init_db.")
        return

    conn = get_connection()
    try:
        with open(SQLITE_SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())  # type: ignore
        print(f"[OK] SQLite database initialized at {DB_PATH}")
    except Exception as e:
        print(f"[WARN] init_db notice: {e}")
    finally:
        conn.close()
