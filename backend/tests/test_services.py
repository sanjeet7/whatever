"""Unit tests for the backend service and HTTP layers."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

from fastapi.testclient import TestClient

SYS_PATH = Path(__file__).resolve().parents[1]
if str(SYS_PATH) not in sys.path:
    sys.path.insert(0, str(SYS_PATH))


from app.api import Application
from app.database import Database
from app.dynamic import DynamicBuilder
from app.orchestration import OrchestrationEngine
from app.registry import RegistryService


def test_registry_and_routing(tmp_path):
    db_path = tmp_path / "agent.db"
    registry = RegistryService(Database(db_path))
    registry.db.reset()

    template = registry.create_agent_template(name="Planner", description="Helps plan")
    tool = registry.create_tool(name="Echo", description="Echo input")
    function = registry.create_function(name="Summarize", description="Summaries")

    instance = registry.create_agent_instance(
        name="PlannerInstance",
        template_id=template.id,
        assigned_tools=[tool.id],
        assigned_functions=[function.id],
        owner_id="user-1",
    )

    engine = OrchestrationEngine(registry=registry)
    result = engine.route_request(user_input="please plan my day", owner_id="user-1")

    assert result.agent_instance_id == instance.id
    assert result.selected_tool_ids == [tool.id]
    assert "PlannerInstance" in result.response


def test_self_improvement_records_proposals(tmp_path):
    db_path = tmp_path / "agent.db"
    registry = RegistryService(Database(db_path))
    registry.db.reset()

    template = registry.create_agent_template(name="Helper", description="Helps")
    registry.create_agent_instance(name="HelperInstance", template_id=template.id, owner_id="owner")

    engine = OrchestrationEngine(registry=registry)
    result = asyncio.run(engine.self_improve(owner_id="owner"))

    assert result["proposals"], result
    proposals = registry.list_improvements()
    assert proposals[0].summary == result["proposals"][0]


def test_dynamic_builder_determinism(tmp_path):
    registry = RegistryService(Database(tmp_path / "agent.db"))
    registry.db.reset()
    builder = DynamicBuilder(registry=registry)

    component = asyncio.run(builder.generate_tool("summarize incidents", {"priority": "high"}))
    validation = asyncio.run(builder.validate_and_test(component))

    assert component.metadata["kind"] == "tool"
    assert validation["status"] == "passed"
    digest = validation["digest"]

    component_again = asyncio.run(builder.generate_tool("summarize incidents", {"priority": "high"}))
    validation_again = asyncio.run(builder.validate_and_test(component_again))
    assert validation_again["digest"] == digest


def test_http_endpoints(tmp_path):
    db = Database(tmp_path / "agent.db")
    app = Application(RegistryService(db))
    client = TestClient(app.api)

    template_payload = {"name": "Planner", "description": "Helps plan"}
    response = client.post("/templates", json=template_payload)
    assert response.status_code == 201, response.text
    template_id = response.json()["id"]

    tool_payload = {"name": "Echo", "description": "Echo input"}
    tool_response = client.post("/tools", json=tool_payload)
    assert tool_response.status_code == 201

    deploy_payload = {"template_id": template_id, "name": "PlannerInstance", "owner_id": "user"}
    deploy_response = client.post("/agents/deploy", json=deploy_payload)
    assert deploy_response.status_code == 201

    route_response = client.post("/route", json={"user_input": "plan", "owner_id": "user"})
    assert route_response.status_code == 200
    assert route_response.json()["agent_instance_id"] == deploy_response.json()["id"]

    improve_response = client.post("/self-improve", params={"owner_id": "user"})
    assert improve_response.status_code == 200
    assert improve_response.json()["proposals"], improve_response.json()
