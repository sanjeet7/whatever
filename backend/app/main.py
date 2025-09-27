"""CLI launcher for the backend API with optional demo seeding."""

from __future__ import annotations

import asyncio
from typing import Any

import uvicorn

from .api import Application


async def seed_demo_data(app: Application) -> dict[str, Any]:
    """Populate the database with a minimal scenario for local testing."""

    app.registry.db.reset()
    template = app.create_template(name="Planner", description="Helps plan tasks")
    tool = app.create_tool(name="Echo", description="Echo user input")
    function = app.create_function(name="Summarize", description="Summaries")
    agent_id = app.deploy_agent(
        template_id=template.id,
        name="PlannerInstance",
        owner_id="demo",
        assigned_tools=[tool.id],
        assigned_functions=[function.id],
    )
    route_result = app.route_request(user_input="plan my day", owner_id="demo")
    improvement = await app.self_improve(owner_id="demo")
    return {
        "template": template,
        "tool": tool,
        "function": function,
        "agent_id": agent_id,
        "route_result": route_result,
        "improvement": improvement,
    }


def main() -> None:
    application = Application()

    results = asyncio.run(seed_demo_data(application))
    print("Seeded data:")
    for key, value in results.items():
        print(f"- {key}: {value}")

    uvicorn.run(application.api, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
