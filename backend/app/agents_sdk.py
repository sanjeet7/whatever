"""OpenAI Agents SDK integration using the official SDK."""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import random
import string
import asyncio

from agents import Agent, function_tool, Runner
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


# Helpers to run sync SDK calls safely from async contexts ---------------------
def _run_sync_with_loop(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run a blocking function that expects an asyncio event loop in a fresh loop.

    Some SDK internals call asyncio.get_running_loop() or similar, which fails in a
    bare thread pool worker. This helper creates and sets a loop for the duration
    of the call to keep those internals happy.
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return func(*args, **kwargs)
    finally:
        try:
            loop.close()
        finally:
            asyncio.set_event_loop(None)

# Tool definitions using the official SDK
@function_tool
def web_search(query: str) -> str:
    """Search the web for information."""
    # In production, integrate with a real search API
    return f"Search results for '{query}': [Mock results - integrate with real search API]"


@function_tool
def analyze_code(code: str, language: str = "python") -> str:
    """Analyze code for improvements and best practices."""
    return f"Code analysis for {language}: The code appears to be functional. Consider adding type hints and documentation."


@function_tool
def generate_content(topic: str, content_type: str = "article") -> str:
    """Generate content on a given topic."""
    return f"Generated {content_type} about {topic}: [Content would be generated here]"


@function_tool
def database_query(query: str, table: str) -> str:
    """Execute a database query (safely)."""
    # In production, implement proper SQL injection prevention
    return f"Query results from {table}: [Mock results]"


@function_tool
def create_agent_config(
    name: str,
    description: str,
    capabilities: List[str],
    model: str = "gpt-5"
) -> Dict[str, Any]:
    """Create a configuration for a new agent based on requirements."""
    
    # Map capabilities to tools
    tool_mapping = {
        "web_search": "Can search the web for information",
        "code_analysis": "Can analyze and improve code",
        "content_generation": "Can generate various types of content",
        "data_access": "Can query databases"
    }
    
    tools = []
    for capability in capabilities:
        if capability in tool_mapping:
            tools.append(capability)
    
    instructions = f"""You are {name}. {description}

Your capabilities include:
{chr(10).join(f'- {tool_mapping.get(cap, cap)}' for cap in capabilities)}

Always be helpful, accurate, and follow best practices in your domain.
"""
    
    return {
        "name": name,
        "instructions": instructions,
        "model": model,
        "tools": tools,
        "metadata": {
            "created_at": datetime.utcnow().isoformat(),
            "capabilities": capabilities
        }
    }


class AgentManager:
    """Manager for creating and running agents using the official SDK."""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tool_registry = {
            "web_search": web_search,
            "code_analysis": analyze_code,
            "content_generation": generate_content,
            "data_access": database_query
        }
        # Start with an empty pool; remove hardcoded demo agents
    
    def _ensure_meta_agent(self) -> None:
        """Create the meta agent lazily if it doesn't exist."""
        if getattr(self, "meta_agent", None) is not None:
            return
        self.meta_agent = Agent(
            name="Meta Agent Designer",
            instructions="""You are a Meta Agent Designer. Your role is to help users create specialized AI agents.

When a user describes what they want an agent to do:
1. Understand the requirements and ask clarifying questions if needed
2. Design the agent's personality, capabilities, and constraints
3. Use the create_agent_config tool to generate the configuration
4. Recommend appropriate tools and model settings
5. Explain how the agent will work

Be creative but practical. Ensure agents are helpful, harmless, and honest.""",
            tools=[create_agent_config],
            model="gpt-5",
        )
        self.agents["meta_agent"] = self.meta_agent

    def _initialize_default_agents(self):
        """Deprecated: defaults removed. Create via API or Meta Agent."""
        return
    
    def create_agent(self, config: Dict[str, Any]) -> str:
        """Create a new agent from configuration."""
        name = config["name"]
        instructions = config["instructions"]
        model = config.get("model", "gpt-5")
        tool_names = config.get("tools", [])
        
        # Map tool names to actual tool functions
        tools = []
        for tool_name in tool_names:
            if tool_name in self.tool_registry:
                tools.append(self.tool_registry[tool_name])
        
        # Create the agent
        agent = Agent(
            name=name,
            instructions=instructions,
            tools=tools,
            model=model
        )
        
        # Store the agent
        agent_id = name.lower().replace(" ", "_")
        self.agents[agent_id] = agent
        
        return agent_id
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents."""
        return [
            {
                "id": agent_id,
                "name": agent.name,
                "model": agent.model,
                "tools": [getattr(tool, 'name', tool.__class__.__name__) for tool in agent.tools] if agent.tools else []
            }
            for agent_id, agent in self.agents.items()
        ]
    
    def run_agent_sync(self, agent_id: str, user_input: str) -> str:
        """Run an agent synchronously."""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        result = Runner.run_sync(
            starting_agent=agent,
            input=user_input
        )
        
        return result.final_output
    
    async def run_agent_async(self, agent_id: str, user_input: str) -> str:
        """Run an agent without blocking the event loop."""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: _run_sync_with_loop(Runner.run_sync, starting_agent=agent, input=user_input),
        )
        return result.final_output
    
    def design_agent_with_meta(self, requirements: str) -> Dict[str, Any]:
        """Use the meta agent to design a new agent (sync helper)."""
        self._ensure_meta_agent()
        result = Runner.run_sync(
            starting_agent=self.meta_agent,
            input=f"Please design an AI agent with these requirements: {requirements}"
        )
        
        # Parse the result to extract the agent configuration
        # In a real implementation, you'd parse the structured output
        unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        unique_name = f"Custom Agent {int(datetime.utcnow().timestamp()*1_000_000)}_{unique_suffix}"
        return {
            "design": result.final_output,
            "suggested_config": {
                "name": unique_name,
                "instructions": "Agent designed based on your requirements",
                "model": "gpt-5",
                "tools": []
            }
        }

    async def design_agent_with_meta_async(self, requirements: str) -> Dict[str, Any]:
        """Async variant to avoid blocking event loop."""
        self._ensure_meta_agent()
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: _run_sync_with_loop(
                Runner.run_sync,
                starting_agent=self.meta_agent,
                input=f"Please design an AI agent with these requirements: {requirements}",
            ),
        )
        unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        unique_name = f"Custom Agent {int(datetime.utcnow().timestamp()*1_000_000)}_{unique_suffix}"
        return {
            "design": result.final_output,
            "suggested_config": {
                "name": unique_name,
                "instructions": "Agent designed based on your requirements",
                "model": "gpt-4-turbo-preview",
                "tools": []
            }
        }


# Pydantic models for API
class AgentCreateRequest(BaseModel):
    """Request to create a new agent."""
    name: str
    instructions: str
    model: str = "gpt-5"
    tools: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentRunRequest(BaseModel):
    """Request to run an agent."""
    agent_id: str
    user_input: str


class MetaAgentDesignRequest(BaseModel):
    """Request to design an agent using the meta agent."""
    requirements: str


class AgentResponse(BaseModel):
    """Response containing agent information."""
    id: str
    name: str
    model: str
    tools: List[str]


class RunResponse(BaseModel):
    """Response from running an agent."""
    agent_id: str
    output: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Example handoff scenarios
class HandoffAgentSystem:
    """System demonstrating agent handoffs."""
    
    def __init__(self):
        # Finance specialist
        @function_tool
        def check_rewards(program: str, category: str) -> str:
            """Look up credit card rewards for a category (mock)."""
            mapping = {
                ("amex_platinum", "hotel"): "5x points on prepaid hotel bookings",
                ("amex_platinum", "airfare"): "5x points on flights booked with airlines",
                ("chase_sapphire_preferred", "dining"): "3x points on dining",
            }
            return mapping.get((program.lower(), category.lower()), "1x base points")

        self.finance_agent = Agent(
            name="Finance Specialist",
            instructions=(
                "You analyze financial statements, optimize credit card rewards, and recommend the most rewarding payment method."
            ),
            tools=[check_rewards],
        )

        # Travel specialist
        @function_tool
        def propose_itinerary(destination: str, nights: int, preference: str = "") -> str:
            """Draft a simple travel itinerary (mock)."""
            return (
                f"Itinerary for {destination} ({nights} nights): Day 1 arrival and local cuisine, Day 2 city tour, "
                f"Day 3 museum and parks, Day 4 optional excursion, Day 5 leisure. Preferences: {preference}."
            )

        self.travel_agent = Agent(
            name="Travel Specialist",
            instructions=(
                "You plan travel itineraries based on schedules, preferences, and loyalty benefits. Coordinate with the Finance Specialist when rewards impact bookings."
            ),
            tools=[propose_itinerary, web_search],
        )

        # Customer support (kept for completeness)
        @function_tool
        def submit_refund_request(item_id: str, reason: str) -> str:
            """Submit a refund request for an item."""
            return f"Refund request submitted for item {item_id}. Reason: {reason}. Reference number: REF-{datetime.now().timestamp()}"

        self.support_agent = Agent(
            name="Support and Returns",
            instructions="You handle customer support issues, especially returns and refunds. Be empathetic and solution-oriented.",
            tools=[submit_refund_request],
        )

        # Shopping assistant
        self.shopping_agent = Agent(
            name="Shopping Assistant",
            instructions="You help users find and purchase products. You can search for products and provide recommendations.",
            tools=[web_search],
        )

        # Triage/Orchestrator agent that routes and coordinates
        self.triage_agent = Agent(
            name="Orchestrator",
            instructions="""
            You are the single entrypoint orchestrator. Determine which specialist(s) should handle the request.
            Principles:
            - Finance, rewards, payments -> Finance Specialist
            - Travel planning, itineraries, bookings -> Travel Specialist
            - If both finance and travel are relevant, coordinate both: first consult Finance for rewards, then Travel for itinerary using those insights.
            - Shopping/product search -> Shopping Assistant
            - Refunds/support -> Support and Returns

            When coordinating multiple specialists, explicitly state the handoff sequence and merge the results in your final response.
            """,
            handoffs=[self.finance_agent, self.travel_agent, self.shopping_agent, self.support_agent],
        )
    
    def handle_request(self, user_input: str) -> str:
        """Handle a user request through the triage system."""
        result = Runner.run_sync(
            starting_agent=self.triage_agent,
            input=user_input
        )
        return result.final_output

    async def handle_request_async(self, user_input: str) -> str:
        """Async variant to avoid blocking event loop."""
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: _run_sync_with_loop(Runner.run_sync, starting_agent=self.triage_agent, input=user_input),
        )
        return result.final_output