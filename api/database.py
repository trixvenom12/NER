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

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, ".."))
_BUNDLED_DB = os.path.join(_CURRENT_DIR, "ner_logistics.db")
_ORIGINAL_DB = (
    _BUNDLED_DB
    if os.path.exists(_BUNDLED_DB)
    else os.path.join(_PROJECT_ROOT, "ner_logistics.db")
    if os.path.exists(os.path.join(_PROJECT_ROOT, "ner_logistics.db"))
    else os.path.join(_PROJECT_ROOT, "data", "ner_logistics.db")
)
SQLITE_SCHEMA_PATH = (
    os.path.join(_CURRENT_DIR, "schema.sql")
    if os.path.exists(os.path.join(_CURRENT_DIR, "schema.sql"))
    else os.path.join(_PROJECT_ROOT, "data", "schema.sql")
)
SUPABASE_SCHEMA_PATH = (
    os.path.join(_CURRENT_DIR, "supabase_schema.sql")
    if os.path.exists(os.path.join(_CURRENT_DIR, "supabase_schema.sql"))
    else os.path.join(_PROJECT_ROOT, "data", "supabase_schema.sql")
)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
except Exception:
    pass

# Read database URL from environment
RAW_DB_URL = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL") or ""
IS_POSTGRES = RAW_DB_URL.startswith("postgres://") or RAW_DB_URL.startswith("postgresql://")

def _setup_sqlite_db() -> str:
    """Finds the best SQLite database file, copying to /tmp in serverless if writable."""
    candidates = [
        _BUNDLED_DB,
        os.path.join(_PROJECT_ROOT, "ner_logistics.db"),
        os.path.join(_PROJECT_ROOT, "data", "ner_logistics.db"),
    ]
    source_file = next((p for p in candidates if os.path.exists(p)), None)

    # In serverless environments (Linux with /tmp), copy DB to /tmp for write access
    if os.path.exists("/tmp") and os.path.isdir("/tmp") and os.name != "nt":
        tmp_target = "/tmp/ner_logistics.db"
        need_copy = not os.path.exists(tmp_target)
        if not need_copy and source_file:
            try:
                if os.path.getsize(tmp_target) < os.path.getsize(source_file):
                    need_copy = True
            except Exception:
                need_copy = True

        if need_copy and source_file:
            try:
                shutil.copy2(source_file, tmp_target)
            except Exception as e:
                print(f"[WARN] Failed copying SQLite DB to /tmp: {e}")

        if os.path.exists(tmp_target):
            return tmp_target

    return source_file or _BUNDLED_DB


if IS_POSTGRES:
    # Standard clean URI for psycopg2 / psycopg
    DATABASE_URL = RAW_DB_URL.replace("postgresql+psycopg2://", "postgresql://", 1).replace("postgres://", "postgresql://", 1)
    DB_PATH = DATABASE_URL

    # For SQLAlchemy 2.0, explicitly specify postgresql+psycopg2 to use psycopg2 driver,
    # or fallback to standard URL if psycopg (v3) is available.
    if RAW_DB_URL.startswith("postgres://"):
        SQL_ALCHEMY_URL = RAW_DB_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif RAW_DB_URL.startswith("postgresql://") and not RAW_DB_URL.startswith("postgresql+"):
        SQL_ALCHEMY_URL = RAW_DB_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        SQL_ALCHEMY_URL = RAW_DB_URL

    try:
        engine = create_engine(SQL_ALCHEMY_URL, pool_pre_ping=True)
    except Exception:
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        except Exception as e:
            print(f"[WARN] SQLAlchemy engine creation deferred/failed: {e}")
            engine = None
else:
    DB_PATH = _setup_sqlite_db()
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    try:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    except Exception:
        engine = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()


class PostgresCursorWrapper:
    """Adapts psycopg2 cursor to mirror sqlite3 cursor semantics (dict access & '?' params)."""
    def __init__(self, raw_cur: Any):
        self._cur = raw_cur
        self.lastrowid = None

    def execute(self, query: str, params: Any = None):
        if params is not None and "?" in query:
            query = query.replace("?", "%s")

        trimmed = query.strip()
        is_insert = trimmed.upper().startswith("INSERT INTO")
        if is_insert and "RETURNING" not in query.upper():
            query_with_returning = trimmed.rstrip(";") + " RETURNING id;"
            try:
                if params is not None:
                    res = self._cur.execute(query_with_returning, params)
                else:
                    res = self._cur.execute(query_with_returning)
                row = self._cur.fetchone()
                if row:
                    self.lastrowid = row.get("id") if isinstance(row, dict) else row[0]
                return res
            except Exception:
                pass

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
        try:
            from psycopg2.extras import RealDictCursor
            return PostgresCursorWrapper(self._conn.cursor(cursor_factory=RealDictCursor))
        except Exception:
            return PostgresCursorWrapper(self._conn.cursor())

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
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            raw = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor, connect_timeout=5)
            return PostgresConnectionWrapper(raw)
        except Exception as e1:
            try:
                import psycopg
                from psycopg.rows import dict_row
                raw = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5)
                return PostgresConnectionWrapper(raw)
            except Exception as e2:
                print(f"[WARN] Supabase Postgres connection failed ({e1} | {e2}); using SQLite fallback.")

    sqlite_path = _setup_sqlite_db()
    conn = None

    try:
        conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
        try:
            conn.execute("PRAGMA foreign_keys=ON;")
        except Exception:
            pass
    except sqlite3.OperationalError:
        # Fallback to read-only URI if running directly on a read-only filesystem (e.g. /var/task)
        clean_path = sqlite_path.replace("\\", "/")
        if not clean_path.startswith("/"):
            clean_path = "/" + clean_path
        conn = sqlite3.connect(f"file:{clean_path}?mode=ro", uri=True, check_same_thread=False)
        conn.row_factory = sqlite3.Row

    # Ensure tables exist (self-healing for Vercel /tmp or cold containers)
    try:
        conn.execute("SELECT 1 FROM facility LIMIT 1;")
    except sqlite3.OperationalError:
        print("[WARN] Table 'facility' missing in connected DB. Refreshing from bundled DB...")
        try:
            conn.close()
        except Exception:
            pass

        if os.path.exists(_BUNDLED_DB) and sqlite_path != _BUNDLED_DB:
            try:
                shutil.copy2(_BUNDLED_DB, sqlite_path)
            except Exception as e:
                print(f"[WARN] Failed to re-copy bundled DB: {e}")
        elif os.path.exists(SQLITE_SCHEMA_PATH):
            try:
                temp_conn = sqlite3.connect(sqlite_path, check_same_thread=False)
                with open(SQLITE_SCHEMA_PATH, "r") as f:
                    temp_conn.executescript(f.read())
                temp_conn.close()
            except Exception as e:
                print(f"[WARN] Failed to run schema on DB: {e}")

        try:
            conn = sqlite3.connect(sqlite_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
        except sqlite3.OperationalError:
            clean_path = sqlite_path.replace("\\", "/")
            if not clean_path.startswith("/"):
                clean_path = "/" + clean_path
            conn = sqlite3.connect(f"file:{clean_path}?mode=ro", uri=True, check_same_thread=False)
            conn.row_factory = sqlite3.Row

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
        try:
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
        except Exception as e:
            print(f"[WARN] Supabase connection during init_db failed: {e}")
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
