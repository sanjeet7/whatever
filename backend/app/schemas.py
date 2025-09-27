"""Shared request/response schemas for the HTTP API and service layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Dataclass helpers used by the dynamic generation stubs
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class GenerationRequest:
    kind: str
    description: str
    context: dict[str, Any]


@dataclass(slots=True)
class GenerationResponse:
    name: str
    code: str
    metadata: dict[str, Any]


@dataclass(slots=True)
class SelfImprovementResponse:
    proposals: list[str]
    generated: dict[str, Any]
    validation: dict[str, Any] | None = None
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Pydantic models for HTTP serialization
# ---------------------------------------------------------------------------


class TemplateCreate(BaseModel):
    name: str
    description: str
    category: str = "general"
    instructions_template: str = ""
    model_config: Dict[str, Any] = Field(default_factory=dict)
    required_tools: List[str] = Field(default_factory=list)
    sample_interactions: List[Dict[str, Any]] = Field(default_factory=list)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    created_by: str = "system"


class TemplateRead(TemplateCreate):
    id: int
    created_at: datetime
    version: int

    model_config = ConfigDict(from_attributes=True)


class ToolCreate(BaseModel):
    name: str
    description: str
    category: str = "general"
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    implementation_code: str = ""
    dependencies: List[str] = Field(default_factory=list)
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    performance_data: Dict[str, Any] = Field(default_factory=dict)
    created_by: str = "system"


class ToolRead(ToolCreate):
    id: int
    created_at: datetime
    version: int

    model_config = ConfigDict(from_attributes=True)


class FunctionCreate(BaseModel):
    name: str
    description: str
    category: str = "general"
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)
    implementation_code: str = ""
    dependencies: List[str] = Field(default_factory=list)
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    created_by: str = "system"


class FunctionRead(FunctionCreate):
    id: int
    created_at: datetime
    version: int

    model_config = ConfigDict(from_attributes=True)


class AgentDeployRequest(BaseModel):
    template_id: int
    name: str
    custom_instructions: str | None = None
    assigned_tools: List[int] | None = None
    assigned_functions: List[int] | None = None
    owner_id: str | None = None


class AgentRead(BaseModel):
    id: int
    template_id: int
    name: str
    custom_instructions: str
    assigned_tools: List[int]
    assigned_functions: List[int]
    status: str
    owner_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentDeployResponse(AgentRead):
    """Response payload for agent deployment operations."""


class RouteRequest(BaseModel):
    user_input: str
    owner_id: str | None = None


class RouteResponse(BaseModel):
    agent_instance_id: int
    selected_tool_ids: List[int]
    response: str

    model_config = ConfigDict(from_attributes=True)


class SelfImproveResponse(BaseModel):
    proposals: List[str]
    generated: Dict[str, Any]
    validation: Dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)
