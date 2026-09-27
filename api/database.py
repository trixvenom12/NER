"""
api/database.py — SQLite Database Connection & Initialization
Provides raw sqlite3 connections with Row factory for dict-like access.
All routers and services depend on get_connection() and init_db().
"""

import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Resolve DB and schema paths relative to project root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(_PROJECT_ROOT, "data", "ner_logistics.db")
SCHEMA_PATH = os.path.join(_PROJECT_ROOT, "data", "schema.sql")

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
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
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
