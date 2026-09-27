"""
api/scripts/migrate_to_supabase.py — Automated SQLite -> Supabase PostgreSQL Migrator
Applies the Supabase schema and transfers all corridor road segments, facilities,
weather points, historical incidents, and risk caches to your Supabase cloud database.

Usage:
    python api/scripts/migrate_to_supabase.py "postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres"
Or set DATABASE_URL in your environment/.env:
    python api/scripts/migrate_to_supabase.py
"""

import os
import sys
import json
import sqlite3
import argparse
from typing import List, Dict, Any

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SQLITE_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "ner_logistics.db")
SCHEMA_SQL_PATH = os.path.join(_PROJECT_ROOT, "data", "supabase_schema.sql")


def run_migration(db_url: str):
    import psycopg2
    from psycopg2.extras import execute_values

    # Normalize url``
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print(f"\n========================================================")
    print(f"🚀 MIGRATING NER LOGISTICS DATA TO SUPABASE")
    print(f"========================================================")
    print(f"[*] Target: {db_url.split('@')[-1] if '@' in db_url else 'Supabase'}")
    print(f"[*] Source SQLite: {SQLITE_DB_PATH}")

    if not os.path.exists(SQLITE_DB_PATH):
        print(f"[ERROR] Source SQLite database not found at {SQLITE_DB_PATH}")
        sys.exit(1)

    # 1. Connect to PostgreSQL
    print("\n[1/4] Connecting to Supabase PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(db_url)
        pg_conn.autocommit = False
        pg_cur = pg_conn.cursor()
        print("  ✓ Connected successfully.")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        print("\nPlease check your Supabase connection string and password.")
        sys.exit(1)

    # 2. Apply Schema
    print("\n[2/4] Applying Supabase schema & RLS policies...")
    if os.path.exists(SCHEMA_SQL_PATH):
        with open(SCHEMA_SQL_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        try:
            pg_cur.execute(schema_sql)
            pg_conn.commit()
            print("  ✓ Tables, indexes, and RLS policies created.")
        except Exception as e:
            pg_conn.rollback()
            print(f"  ⚠ Schema notice: {e}")
    else:
        print(f"  ⚠ Schema file not found at {SCHEMA_SQL_PATH}")

    # 3. Read SQLite and Transfer
    print("\n[3/4] Migrating data from SQLite...")
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    tables = ["segment", "facility", "weather_obs", "incident", "segment_risk", "report"]
    stats = {}

    for table in tables:
        sqlite_cur.execute(f"SELECT * FROM {table};")
        rows = sqlite_cur.fetchall()
        if not rows:
            stats[table] = 0
            continue

        columns = list(rows[0].keys())
        col_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        # Prepare values
        values_to_insert = []
        for r in rows:
            row_vals = []
            for col in columns:
                val = r[col]
                # If factors or attrs is a JSON string, ensure valid format
                if col in ("factors", "attrs") and isinstance(val, str):
                    try:
                        val = json.dumps(json.loads(val))
                    except Exception:
                        pass
                row_vals.append(val)
            values_to_insert.append(tuple(row_vals))

        # Clear existing table data in Supabase before migrating fresh copy
        pg_cur.execute(f"DELETE FROM {table};")

        insert_sql = f"INSERT INTO {table} ({col_names}) VALUES %s ON CONFLICT DO NOTHING;"
        execute_values(pg_cur, f"INSERT INTO {table} ({col_names}) VALUES %s", values_to_insert)
        stats[table] = len(values_to_insert)
        print(f"  ✓ {table:<15} : {len(values_to_insert)} rows migrated")

    # Reset sequences for auto-increment IDs
    print("\n[4/4] Aligning PostgreSQL ID sequences...")
    for table in ["segment", "facility", "weather_obs", "incident", "report"]:
        try:
            pg_cur.execute(f"SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 1));")
        except Exception:
            pass

    pg_conn.commit()
    sqlite_conn.close()
    pg_conn.close()

    print("\n========================================================")
    print("✅ MIGRATION COMPLETED SUCCESSFULLY")
    print("========================================================")
    for tbl, cnt in stats.items():
        print(f"  • {tbl:<16}: {cnt} records in Supabase")
    print("========================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate SQLite to Supabase PostgreSQL")
    parser.add_argument("db_url", nargs="?", default=None, help="Supabase PostgreSQL connection URI")
    args = parser.parse_args()

    target_url = args.db_url or os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")

    if not target_url:
        print("[ERROR] No DATABASE_URL provided.")
        print("Usage:")
        print("  python api/scripts/migrate_to_supabase.py \"postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres\"")
        sys.exit(1)

    run_migration(target_url)
