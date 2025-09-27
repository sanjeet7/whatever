"""Dataclasses representing registry records for the agent platform."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence


@dataclass(slots=True)
class AgentTemplate:
    id: int
    name: str
    category: str
    description: str
    instructions_template: str
    model_config: Mapping[str, Any]
    required_tools: Sequence[str]
    sample_interactions: Sequence[Mapping[str, Any]]
    performance_metrics: Mapping[str, Any]
    created_by: str
    created_at: datetime
    version: int


@dataclass(slots=True)
class Tool:
    id: int
    name: str
    category: str
    description: str
    input_schema: Mapping[str, Any]
    implementation_code: str
    dependencies: Sequence[str]
    test_cases: Sequence[Mapping[str, Any]]
    performance_data: Mapping[str, Any]
    created_by: str
    created_at: datetime
    version: int


@dataclass(slots=True)
class Function:
    id: int
    name: str
    category: str
    description: str
    parameters_schema: Mapping[str, Any]
    implementation_code: str
    dependencies: Sequence[str]
    test_cases: Sequence[Mapping[str, Any]]
    created_by: str
    created_at: datetime
    version: int


@dataclass(slots=True)
class AgentInstance:
    id: int
    name: str
    template_id: int
    custom_instructions: str
    assigned_tools: Sequence[int]
    assigned_functions: Sequence[int]
    status: str
    owner_id: str | None
    created_at: datetime


@dataclass(slots=True)
class ImprovementProposal:
    id: int
    agent_instance_id: int | None
    proposal_type: str
    summary: str
    created_at: datetime


@dataclass(slots=True)
class ChatSession:
    id: int
    session_id: str
    user: str
    created_at: datetime


@dataclass(slots=True)
class ChatMessage:
    id: int
    session_id: str
    role: str
    content: str
    agent_id: str | None
    created_at: datetime
