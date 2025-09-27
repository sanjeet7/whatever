"""Registry service built on top of the SQLite database."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Sequence

from .database import Database
from .models import AgentInstance, AgentTemplate, Function, ImprovementProposal, Tool, ChatSession, ChatMessage

JsonLike = dict[str, Any] | list[Any]


class RegistryService:
    """CRUD layer for templates, tools, functions, and agent instances."""

    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database()

    # Template operations -----------------------------------------------------------------
    def create_agent_template(
        self,
        *,
        name: str,
        description: str,
        category: str = "general",
        instructions_template: str = "",
        model_config: JsonLike | None = None,
        required_tools: Sequence[str] | None = None,
        sample_interactions: Sequence[JsonLike] | None = None,
        performance_metrics: JsonLike | None = None,
        created_by: str = "system",
    ) -> AgentTemplate:
        with self.db.session() as conn:
            conn.execute(
                """
                INSERT INTO agent_templates (
                    name, category, description, instructions_template, model_config,
                    required_tools, sample_interactions, performance_metrics, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    category=excluded.category,
                    description=excluded.description,
                    instructions_template=excluded.instructions_template,
                    model_config=excluded.model_config,
                    required_tools=excluded.required_tools,
                    sample_interactions=excluded.sample_interactions,
                    performance_metrics=excluded.performance_metrics,
                    created_by=excluded.created_by,
                    created_at=CURRENT_TIMESTAMP,
                    version=agent_templates.version + 1
                """,
                (
                    name,
                    category,
                    description,
                    instructions_template,
                    json.dumps(model_config or {}),
                    json.dumps(list(required_tools or [])),
                    json.dumps(list(sample_interactions or [])),
                    json.dumps(performance_metrics or {}),
                    created_by,
                ),
            )
            row = conn.execute(
                "SELECT * FROM agent_templates WHERE name = ?",
                (name,),
            ).fetchone()
        return self._row_to_template(row)

    def list_agent_templates(self) -> list[AgentTemplate]:
        with self.db.session() as conn:
            rows = conn.execute("SELECT * FROM agent_templates ORDER BY id").fetchall()
        return [self._row_to_template(row) for row in rows]

    def get_agent_template(self, template_id: int) -> AgentTemplate | None:
        with self.db.session() as conn:
            row = conn.execute("SELECT * FROM agent_templates WHERE id = ?", (template_id,)).fetchone()
        return self._row_to_template(row) if row else None

    # Tool operations ---------------------------------------------------------------------
    def create_tool(
        self,
        *,
        name: str,
        description: str,
        category: str = "general",
        input_schema: JsonLike | None = None,
        implementation_code: str = "",
        dependencies: Sequence[str] | None = None,
        test_cases: Sequence[JsonLike] | None = None,
        performance_data: JsonLike | None = None,
        created_by: str = "system",
    ) -> Tool:
        with self.db.session() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tool_registry (
                    name, category, description, input_schema, implementation_code,
                    dependencies, test_cases, performance_data, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    category,
                    description,
                    json.dumps(input_schema or {}),
                    implementation_code,
                    json.dumps(list(dependencies or [])),
                    json.dumps(list(test_cases or [])),
                    json.dumps(performance_data or {}),
                    created_by,
                ),
            )
            tool_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM tool_registry WHERE id = ?", (tool_id,)).fetchone()
        return self._row_to_tool(row)

    def list_tools(self) -> list[Tool]:
        with self.db.session() as conn:
            rows = conn.execute("SELECT * FROM tool_registry ORDER BY id").fetchall()
        return [self._row_to_tool(row) for row in rows]

    # Function operations -----------------------------------------------------------------
    def create_function(
        self,
        *,
        name: str,
        description: str,
        category: str = "general",
        parameters_schema: JsonLike | None = None,
        implementation_code: str = "",
        dependencies: Sequence[str] | None = None,
        test_cases: Sequence[JsonLike] | None = None,
        created_by: str = "system",
    ) -> Function:
        with self.db.session() as conn:
            cursor = conn.execute(
                """
                INSERT INTO function_registry (
                    name, category, description, parameters_schema, implementation_code,
                    dependencies, test_cases, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    category,
                    description,
                    json.dumps(parameters_schema or {}),
                    implementation_code,
                    json.dumps(list(dependencies or [])),
                    json.dumps(list(test_cases or [])),
                    created_by,
                ),
            )
            function_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM function_registry WHERE id = ?", (function_id,)).fetchone()
        return self._row_to_function(row)

    def list_functions(self) -> list[Function]:
        with self.db.session() as conn:
            rows = conn.execute("SELECT * FROM function_registry ORDER BY id").fetchall()
        return [self._row_to_function(row) for row in rows]

    # Agent instances ---------------------------------------------------------------------
    def create_agent_instance(
        self,
        *,
        name: str,
        template_id: int,
        custom_instructions: str = "",
        assigned_tools: Sequence[int] | None = None,
        assigned_functions: Sequence[int] | None = None,
        status: str = "active",
        owner_id: str | None = None,
    ) -> AgentInstance:
        with self.db.session() as conn:
            cursor = conn.execute(
                """
                INSERT INTO agent_instances (
                    name, template_id, custom_instructions, assigned_tools,
                    assigned_functions, status, owner_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    template_id,
                    custom_instructions,
                    json.dumps(list(assigned_tools or [])),
                    json.dumps(list(assigned_functions or [])),
                    status,
                    owner_id,
                ),
            )
            instance_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM agent_instances WHERE id = ?", (instance_id,)).fetchone()
        return self._row_to_instance(row)

    def list_agent_instances(self, owner_id: str | None = None) -> list[AgentInstance]:
        query = "SELECT * FROM agent_instances"
        params: list[Any] = []
        if owner_id:
            query += " WHERE owner_id = ?"
            params.append(owner_id)
        query += " ORDER BY id"
        with self.db.session() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_instance(row) for row in rows]

    def get_agent_instance(self, instance_id: int) -> AgentInstance | None:
        with self.db.session() as conn:
            row = conn.execute("SELECT * FROM agent_instances WHERE id = ?", (instance_id,)).fetchone()
        return self._row_to_instance(row) if row else None

    def record_improvement(
        self,
        *,
        agent_instance_id: int | None,
        proposal_type: str,
        summary: str,
    ) -> ImprovementProposal:
        with self.db.session() as conn:
            cursor = conn.execute(
                """
                INSERT INTO improvement_proposals (agent_instance_id, proposal_type, summary)
                VALUES (?, ?, ?)
                """,
                (agent_instance_id, proposal_type, summary),
            )
            proposal_id = cursor.lastrowid
            row = conn.execute(
                "SELECT * FROM improvement_proposals WHERE id = ?",
                (proposal_id,),
            ).fetchone()
        return self._row_to_proposal(row)

    def list_improvements(self, agent_instance_id: int | None = None) -> list[ImprovementProposal]:
        query = "SELECT * FROM improvement_proposals"
        params: list[Any] = []
        if agent_instance_id is not None:
            query += " WHERE agent_instance_id = ?"
            params.append(agent_instance_id)
        query += " ORDER BY id"
        with self.db.session() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_proposal(row) for row in rows]

    # Chat sessions ----------------------------------------------------------------------
    def create_chat_session(self, *, session_id: str, user: str) -> ChatSession:
        with self.db.session() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO chat_sessions (session_id, user)
                VALUES (?, ?)
                """,
                (session_id, user),
            )
            row = conn.execute(
                "SELECT * FROM chat_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return self._row_to_chat_session(row)

    def get_chat_session(self, session_id: str) -> ChatSession | None:
        with self.db.session() as conn:
            row = conn.execute(
                "SELECT * FROM chat_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return self._row_to_chat_session(row) if row else None

    def append_chat_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        agent_id: str | None = None,
    ) -> ChatMessage:
        with self.db.session() as conn:
            cursor = conn.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, agent_id)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, agent_id),
            )
            message_id = cursor.lastrowid
            row = conn.execute(
                "SELECT * FROM chat_messages WHERE id = ?",
                (message_id,),
            ).fetchone()
        return self._row_to_chat_message(row)

    def list_chat_messages(self, session_id: str, limit: int | None = 200) -> list[ChatMessage]:
        query = "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY id DESC"
        params: list[Any] = [session_id]
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        with self.db.session() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_chat_message(row) for row in reversed(rows)]

    # Conversion helpers ------------------------------------------------------------------
    def _row_to_template(self, row: Any) -> AgentTemplate:
        data = dict(row)
        return AgentTemplate(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            description=data["description"],
            instructions_template=data["instructions_template"],
            model_config=json.loads(data["model_config"] or "{}"),
            required_tools=json.loads(data["required_tools"] or "[]"),
            sample_interactions=json.loads(data["sample_interactions"] or "[]"),
            performance_metrics=json.loads(data["performance_metrics"] or "{}"),
            created_by=data["created_by"],
            created_at=_to_datetime(data["created_at"]),
            version=data["version"],
        )

    def _row_to_tool(self, row: Any) -> Tool:
        data = dict(row)
        return Tool(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            description=data["description"],
            input_schema=json.loads(data["input_schema"] or "{}"),
            implementation_code=data["implementation_code"],
            dependencies=json.loads(data["dependencies"] or "[]"),
            test_cases=json.loads(data["test_cases"] or "[]"),
            performance_data=json.loads(data["performance_data"] or "{}"),
            created_by=data["created_by"],
            created_at=_to_datetime(data["created_at"]),
            version=data["version"],
        )

    def _row_to_function(self, row: Any) -> Function:
        data = dict(row)
        return Function(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            description=data["description"],
            parameters_schema=json.loads(data["parameters_schema"] or "{}"),
            implementation_code=data["implementation_code"],
            dependencies=json.loads(data["dependencies"] or "[]"),
            test_cases=json.loads(data["test_cases"] or "[]"),
            created_by=data["created_by"],
            created_at=_to_datetime(data["created_at"]),
            version=data["version"],
        )

    def _row_to_instance(self, row: Any) -> AgentInstance:
        data = dict(row)
        return AgentInstance(
            id=data["id"],
            name=data["name"],
            template_id=data["template_id"],
            custom_instructions=data["custom_instructions"],
            assigned_tools=json.loads(data["assigned_tools"] or "[]"),
            assigned_functions=json.loads(data["assigned_functions"] or "[]"),
            status=data["status"],
            owner_id=data["owner_id"],
            created_at=_to_datetime(data["created_at"]),
        )

    def _row_to_proposal(self, row: Any) -> ImprovementProposal:
        data = dict(row)
        return ImprovementProposal(
            id=data["id"],
            agent_instance_id=data["agent_instance_id"],
            proposal_type=data["proposal_type"],
            summary=data["summary"],
            created_at=_to_datetime(data["created_at"]),
        )

    def _row_to_chat_session(self, row: Any) -> ChatSession:
        data = dict(row)
        return ChatSession(
            id=data["id"],
            session_id=data["session_id"],
            user=data["user"],
            created_at=_to_datetime(data["created_at"]),
        )

    def _row_to_chat_message(self, row: Any) -> ChatMessage:
        data = dict(row)
        return ChatMessage(
            id=data["id"],
            session_id=data["session_id"],
            role=data["role"],
            content=data["content"],
            agent_id=data.get("agent_id"),
            created_at=_to_datetime(data["created_at"]),
        )


def _to_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)
