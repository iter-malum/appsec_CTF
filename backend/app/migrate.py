"""Lightweight schema upgrades for existing Postgres volumes."""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def migrate_schema(engine: Engine) -> None:
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS university VARCHAR(256)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS course VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS study_program VARCHAR(256)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_extra VARCHAR(256)",
        "ALTER TABLE event_content ADD COLUMN IF NOT EXISTS ends_at TIMESTAMPTZ",
    ]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
