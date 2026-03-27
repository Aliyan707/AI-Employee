"""
database/migrate.py — Migration runner for CS AI FTE.

Supports:
  python database/migrate.py up           — apply all unapplied migrations
  python database/migrate.py down <name>  — roll back named migration
  python database/migrate.py reset        — roll back all, then apply all
  python database/migrate.py status       — show migration status
"""

import sys
import glob
import psycopg2
from pathlib import Path

# Add the repo root to sys.path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

SCHEMA_MIGRATIONS_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id          SERIAL      PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    applied_at  TIMESTAMPTZ  DEFAULT NOW()
);
"""


def get_connection():
    """Create a synchronous psycopg2 connection for migration operations."""
    settings = get_settings()
    return psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )


def ensure_schema_migrations_table(conn):
    """Create the schema_migrations tracking table if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute(SCHEMA_MIGRATIONS_DDL)
    conn.commit()


def get_applied_migrations(conn) -> list[str]:
    """Return list of already-applied migration names."""
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM schema_migrations ORDER BY applied_at")
        return [row[0] for row in cur.fetchall()]


def get_all_migration_files() -> list[tuple[str, Path]]:
    """
    Return sorted list of (name, path) tuples for all UP migrations.
    Excludes _down.sql files.
    """
    pattern = str(MIGRATIONS_DIR / "*.sql")
    files = sorted(glob.glob(pattern))
    result = []
    for f in files:
        path = Path(f)
        name = path.stem  # filename without .sql
        if not name.endswith("_down"):
            result.append((name, path))
    return result


def apply_migration(conn, name: str, path: Path):
    """Apply a single UP migration and record it in schema_migrations."""
    print(f"  Applying: {name}")
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            "INSERT INTO schema_migrations (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
            (name,),
        )
    conn.commit()
    print(f"  Applied:  {name} ✓")


def rollback_migration(conn, name: str):
    """Apply the DOWN migration for the given name."""
    down_path = MIGRATIONS_DIR / f"{name}_down.sql"
    if not down_path.exists():
        print(f"  ERROR: Down migration not found: {down_path}")
        sys.exit(1)
    print(f"  Rolling back: {name}")
    sql = down_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute("DELETE FROM schema_migrations WHERE name = %s", (name,))
    conn.commit()
    print(f"  Rolled back: {name} ✓")


def cmd_up():
    """Apply all unapplied migrations in order."""
    conn = get_connection()
    try:
        ensure_schema_migrations_table(conn)
        applied = set(get_applied_migrations(conn))
        all_migrations = get_all_migration_files()

        pending = [(n, p) for n, p in all_migrations if n not in applied]
        if not pending:
            print("No pending migrations. Database is up to date.")
            return

        print(f"Applying {len(pending)} migration(s)...")
        for name, path in pending:
            apply_migration(conn, name, path)
        print(f"\nDone. {len(pending)} migration(s) applied.")
    finally:
        conn.close()


def cmd_down(migration_name: str):
    """Roll back a specific named migration."""
    conn = get_connection()
    try:
        ensure_schema_migrations_table(conn)
        applied = get_applied_migrations(conn)

        if migration_name not in applied:
            print(f"Migration '{migration_name}' is not applied. Nothing to roll back.")
            return

        rollback_migration(conn, migration_name)
        print(f"\nDone. Migration '{migration_name}' rolled back.")
    finally:
        conn.close()


def cmd_reset():
    """Roll back all migrations then re-apply all."""
    conn = get_connection()
    try:
        ensure_schema_migrations_table(conn)
        applied = list(reversed(get_applied_migrations(conn)))

        if applied:
            print(f"Rolling back {len(applied)} migration(s)...")
            for name in applied:
                rollback_migration(conn, name)
        else:
            print("No migrations to roll back.")
    finally:
        conn.close()

    print("\nRe-applying all migrations...")
    cmd_up()


def cmd_status():
    """Show which migrations have been applied."""
    conn = get_connection()
    try:
        ensure_schema_migrations_table(conn)
        applied = set(get_applied_migrations(conn))
        all_migrations = get_all_migration_files()

        print(f"{'Status':<10} {'Migration':<40}")
        print("-" * 50)
        for name, _ in all_migrations:
            status = "applied" if name in applied else "pending"
            print(f"{status:<10} {name}")
    finally:
        conn.close()


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("up", "down", "reset", "status"):
        print("Usage:")
        print("  python database/migrate.py up")
        print("  python database/migrate.py down <migration_name>")
        print("  python database/migrate.py reset")
        print("  python database/migrate.py status")
        sys.exit(1)

    command = args[0]

    if command == "up":
        cmd_up()
    elif command == "down":
        if len(args) < 2:
            print("Error: 'down' requires a migration name.")
            print("Example: python database/migrate.py down 006_idempotency")
            sys.exit(1)
        cmd_down(args[1])
    elif command == "reset":
        cmd_reset()
    elif command == "status":
        cmd_status()


if __name__ == "__main__":
    main()
