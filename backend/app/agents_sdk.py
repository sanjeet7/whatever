"""OpenAI Agents SDK integration using the official SDK."""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import asyncio

from agents import Agent, function_tool, Runner
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


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
    model: str = "gpt-4-turbo-preview"
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
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Initialize default agents including the meta agent."""
        
        # Meta Agent for designing other agents
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
            model="gpt-4-turbo-preview"
        )
        self.agents["meta_agent"] = self.meta_agent
        
        # Customer Support Agent
        self.support_agent = Agent(
            name="Customer Support",
            instructions="""You are a helpful customer support agent. 
            You can help with product questions, troubleshooting, and general inquiries.
            Always be polite, empathetic, and solution-oriented.""",
            tools=[web_search],
            model="gpt-4-turbo-preview"
        )
        self.agents["support_agent"] = self.support_agent
        
        # Code Assistant Agent
        self.code_agent = Agent(
            name="Code Assistant",
            instructions="""You are an expert programming assistant.
            You can help with code reviews, debugging, and suggesting improvements.
            Support multiple programming languages and follow best practices.""",
            tools=[analyze_code, web_search],
            model="gpt-4-turbo-preview"
        )
        self.agents["code_agent"] = self.code_agent
        
        # Content Creator Agent
        self.content_agent = Agent(
            name="Content Creator",
            instructions="""You are a creative content generator.
            You can help create articles, social media posts, and other content.
            Focus on engaging, original, and well-structured content.""",
            tools=[generate_content, web_search],
            model="gpt-4-turbo-preview"
        )
        self.agents["content_agent"] = self.content_agent
    
    def create_agent(self, config: Dict[str, Any]) -> str:
        """Create a new agent from configuration."""
        name = config["name"]
        instructions = config["instructions"]
        model = config.get("model", "gpt-4-turbo-preview")
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
                "tools": [tool.__name__ for tool in agent.tools] if agent.tools else []
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
        """Run an agent asynchronously."""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        result = await Runner.run_async(
            starting_agent=agent,
            input=user_input
        )
        
        return result.final_output
    
    def design_agent_with_meta(self, requirements: str) -> Dict[str, Any]:
        """Use the meta agent to design a new agent."""
        result = Runner.run_sync(
            starting_agent=self.meta_agent,
            input=f"Please design an AI agent with these requirements: {requirements}"
        )
        
        # Parse the result to extract the agent configuration
        # In a real implementation, you'd parse the structured output
        return {
            "design": result.final_output,
            "suggested_config": {
                "name": "Custom Agent",
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
    model: str = "gpt-4-turbo-preview"
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
        # Shopping assistant
        self.shopping_agent = Agent(
            name="Shopping Assistant",
            instructions="You help users find and purchase products. You can search for products and provide recommendations.",
            tools=[web_search]
        )
        
        # Support agent with refund capability
        @function_tool
        def submit_refund_request(item_id: str, reason: str) -> str:
            """Submit a refund request for an item."""
            return f"Refund request submitted for item {item_id}. Reason: {reason}. Reference number: REF-{datetime.now().timestamp()}"
        
        self.support_agent = Agent(
            name="Support & Returns",
            instructions="You handle customer support issues, especially returns and refunds. Be empathetic and solution-oriented.",
            tools=[submit_refund_request]
        )
        
        # Triage agent that routes to others
        self.triage_agent = Agent(
            name="Triage Agent",
            instructions="""You are the first point of contact. Understand what the user needs and route them to the appropriate specialist:
            - For product searches and shopping: handoff to Shopping Assistant
            - For returns, refunds, and support issues: handoff to Support & Returns
            
            Always explain who you're connecting them with and why.""",
            handoffs=[self.shopping_agent, self.support_agent]
        )
    
    def handle_request(self, user_input: str) -> str:
        """Handle a user request through the triage system."""
        result = Runner.run_sync(
            starting_agent=self.triage_agent,
            input=user_input
        )
        return result.final_output