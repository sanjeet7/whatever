"""Agent orchestration and self-improvement workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .dynamic import DynamicBuilder
from .registry import RegistryService
from .agents_sdk import AgentManager, HandoffAgentSystem


@dataclass(slots=True)
class RouteResult:
    agent_instance_id: int
    selected_tool_ids: list[int]
    response: str


class OrchestrationEngine:
    """High-level coordinator that deploys agents and drives improvements."""

    def __init__(self, registry: RegistryService | None = None, builder: DynamicBuilder | None = None) -> None:
        self.registry = registry or RegistryService()
        self.builder = builder or DynamicBuilder(registry=self.registry)
        # Unified orchestrator talks to handoff system first, then agent manager
        self.agent_manager = AgentManager()
        self.handoff_system = HandoffAgentSystem()

    def deploy_agent(
        self,
        *,
        template_id: int,
        name: str,
        custom_instructions: str | None = None,
        assigned_tools: list[int] | None = None,
        assigned_functions: list[int] | None = None,
        status: str = "active",
        owner_id: str | None = None,
    ) -> int:
        instance = self.registry.create_agent_instance(
            name=name,
            template_id=template_id,
            custom_instructions=custom_instructions or "",
            assigned_tools=assigned_tools or [],
            assigned_functions=assigned_functions or [],
            status=status,
            owner_id=owner_id,
        )
        return instance.id

    def route_request(self, *, user_input: str, owner_id: str | None = None) -> RouteResult:
        """Route a request via orchestrator: triage -> specialist(s) -> response.

        For now, we reuse the built-in triage/handoff system to decide a path.
        If it chooses a specialist, we also record the agent_id equivalently.
        """
        # Try triage handoff first to determine category and response
        output = self.handoff_system.handle_request(user_input)
        # Fallback to a simple agent if needed
        instances = self.registry.list_agent_instances(owner_id=owner_id)
        selected_id = instances[0].id if instances else -1
        tool_ids: list[int] = list(instances[0].assigned_tools) if instances else []
        return RouteResult(agent_instance_id=selected_id, selected_tool_ids=tool_ids, response=output)

    async def self_improve(self, owner_id: str | None = None) -> dict[str, Any]:
        instances = self.registry.list_agent_instances(owner_id=owner_id)
        if not instances:
            component = await self.builder.generate_agent("fallback assistant", ["answer"], {})
            proposal = self.registry.record_improvement(
                agent_instance_id=None,
                proposal_type="agent",
                summary=f"Suggest creating {component.name}",
            )
            return {"proposals": [proposal.summary], "generated": component.metadata}

        instance = instances[0]
        description = f"improve {instance.name}"
        component = await self.builder.generate_tool(description, {"instance": instance.id})
        proposal = self.registry.record_improvement(
            agent_instance_id=instance.id,
            proposal_type="tool",
            summary=f"Add tool {component.name} to agent {instance.name}",
        )
        validation = await self.builder.validate_and_test(component)
        return {
            "proposals": [proposal.summary],
            "generated": component.metadata,
            "validation": validation,
        }


def _match_score(instance, user_input: str) -> int:
    keywords = [instance.name.lower(), instance.status.lower()] + [str(t) for t in instance.assigned_tools]
    return max((len(word) for word in keywords if word in user_input.lower()), default=0)
