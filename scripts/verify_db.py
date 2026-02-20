import os
import sys

from sqlalchemy import create_engine, text

REQUIRED_TABLES = {
    "classifications",
    "users",
    "documents",
    "document_versions",
    "audit_logs",
}


def main() -> int:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2

    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

        rows = conn.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
        ).fetchall()

    present = {r[0] for r in rows}
    missing = sorted(REQUIRED_TABLES - present)
    if missing:
        print(f"Missing tables: {', '.join(missing)}", file=sys.stderr)
        return 1

    print("Database OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
