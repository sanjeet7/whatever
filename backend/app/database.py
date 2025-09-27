"""SQLite helpers for the dynamic agent platform backend."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "agent_platform.db"


class Database:
    """Small wrapper around sqlite3 with automatic schema creation."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_DB_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:  # pragma: no cover - defensive rollback path
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self.session() as conn:
            conn.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS agent_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    category TEXT DEFAULT 'general',
                    description TEXT NOT NULL,
                    instructions_template TEXT DEFAULT '',
                    model_config TEXT DEFAULT '{}',
                    required_tools TEXT DEFAULT '[]',
                    sample_interactions TEXT DEFAULT '[]',
                    performance_metrics TEXT DEFAULT '{}',
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS tool_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    category TEXT DEFAULT 'general',
                    description TEXT NOT NULL,
                    input_schema TEXT DEFAULT '{}',
                    implementation_code TEXT DEFAULT '',
                    dependencies TEXT DEFAULT '[]',
                    test_cases TEXT DEFAULT '[]',
                    performance_data TEXT DEFAULT '{}',
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS function_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    category TEXT DEFAULT 'general',
                    description TEXT NOT NULL,
                    parameters_schema TEXT DEFAULT '{}',
                    implementation_code TEXT DEFAULT '',
                    dependencies TEXT DEFAULT '[]',
                    test_cases TEXT DEFAULT '[]',
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS agent_instances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    template_id INTEGER NOT NULL REFERENCES agent_templates(id) ON DELETE CASCADE,
                    custom_instructions TEXT DEFAULT '',
                    assigned_tools TEXT DEFAULT '[]',
                    assigned_functions TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'active',
                    owner_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS improvement_proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_instance_id INTEGER REFERENCES agent_instances(id) ON DELETE CASCADE,
                    proposal_type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def reset(self) -> None:
        """Drop user data while keeping the schema intact (used in tests)."""

        with self.session() as conn:
            conn.executescript(
                """
                DELETE FROM improvement_proposals;
                DELETE FROM agent_instances;
                DELETE FROM function_registry;
                DELETE FROM tool_registry;
                DELETE FROM agent_templates;
                """
            )
