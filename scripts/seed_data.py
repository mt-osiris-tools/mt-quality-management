import os
import sys

from sqlalchemy import create_engine, text

SEED_CLASSIFICATIONS = [
    (
        0,
        "Public",
        "Approved for external release. No access restrictions.",
        "Standard document handling. No special protection required.",
    ),
    (
        1,
        "Internal",
        "Internal use only. Authenticated users with clearance level 1+.",
        "Keep within organization. Do not share externally without approval.",
    ),
    (
        2,
        "Confidential",
        "Restricted business information. Users with clearance level 2+.",
        "Encrypt at rest and in transit. Limit distribution. Log all access.",
    ),
    (
        3,
        "Restricted",
        "Need-to-know basis only. Clearance level 3+.",
        "Maximum protection. Access requires justification and auditing.",
    ),
]


def main() -> int:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2

    engine = create_engine(database_url, pool_pre_ping=True)
    insert_stmt = text(
        """
        INSERT INTO classifications (
            level_code,
            level_name,
            access_rules,
            handling_requirements
        )
        VALUES (:level_code, :level_name, :access_rules, :handling_requirements)
        ON CONFLICT (level_code) DO NOTHING
        """
    )

    with engine.begin() as conn:
        for (
            level_code,
            level_name,
            access_rules,
            handling_requirements,
        ) in SEED_CLASSIFICATIONS:
            conn.execute(
                insert_stmt,
                {
                    "level_code": level_code,
                    "level_name": level_name,
                    "access_rules": access_rules,
                    "handling_requirements": handling_requirements,
                },
            )

    print("Seed complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
