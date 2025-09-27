"""OpenAI Agents SDK integration for the dynamic agent platform."""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentConfig:
    """Configuration for an OpenAI agent."""
    name: str
    instructions: str
    model: str = "gpt-4-turbo-preview"
    tools: List[Dict[str, Any]] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    metadata: Dict[str, Any] = None


class OpenAIAgentManager:
    """Manager for OpenAI agents using the Assistants API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self._assistants: Dict[str, Any] = {}
        self._threads: Dict[str, Any] = {}
    
    def create_agent(self, config: AgentConfig) -> str:
        """Create a new OpenAI assistant (agent)."""
        tools = config.tools or []
        
        # Add code interpreter by default
        if not any(tool.get("type") == "code_interpreter" for tool in tools):
            tools.append({"type": "code_interpreter"})
        
        assistant = self.client.beta.assistants.create(
            name=config.name,
            instructions=config.instructions,
            model=config.model,
            tools=tools,
            temperature=config.temperature,
            metadata=config.metadata or {}
        )
        
        self._assistants[assistant.id] = assistant
        return assistant.id
    
    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Any:
        """Update an existing agent."""
        assistant = self.client.beta.assistants.update(
            agent_id,
            **updates
        )
        self._assistants[agent_id] = assistant
        return assistant
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        try:
            self.client.beta.assistants.delete(agent_id)
            self._assistants.pop(agent_id, None)
            return True
        except Exception:
            return False
    
    def list_agents(self) -> List[Any]:
        """List all agents."""
        return list(self.client.beta.assistants.list())
    
    def create_thread(self, messages: Optional[List[Dict[str, str]]] = None) -> str:
        """Create a new conversation thread."""
        thread = self.client.beta.threads.create(
            messages=messages or []
        )
        self._threads[thread.id] = thread
        return thread.id
    
    def add_message(self, thread_id: str, content: str, role: str = "user") -> Any:
        """Add a message to a thread."""
        message = self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=content
        )
        return message
    
    def run_agent(self, agent_id: str, thread_id: str, 
                  additional_instructions: Optional[str] = None) -> Any:
        """Run an agent on a thread."""
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=agent_id,
            instructions=additional_instructions
        )
        
        # Wait for completion
        while run.status in ["queued", "in_progress"]:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        return run
    
    def get_messages(self, thread_id: str) -> List[Any]:
        """Get all messages in a thread."""
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        return list(messages)
    
    def create_function_tool(self, name: str, description: str, 
                           parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a function tool definition."""
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }


class ToolBuilder:
    """Builder for creating OpenAI function tools."""
    
    @staticmethod
    def create_web_search_tool() -> Dict[str, Any]:
        """Create a web search tool."""
        return {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    @staticmethod
    def create_database_query_tool() -> Dict[str, Any]:
        """Create a database query tool."""
        return {
            "type": "function",
            "function": {
                "name": "database_query",
                "description": "Query the database for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "The table to query"
                        },
                        "query": {
                            "type": "string",
                            "description": "SQL query to execute"
                        }
                    },
                    "required": ["table", "query"]
                }
            }
        }
    
    @staticmethod
    def create_api_call_tool() -> Dict[str, Any]:
        """Create an API call tool."""
        return {
            "type": "function",
            "function": {
                "name": "api_call",
                "description": "Make an API call to external services",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The API endpoint URL"
                        },
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST", "PUT", "DELETE"],
                            "description": "HTTP method"
                        },
                        "headers": {
                            "type": "object",
                            "description": "Request headers"
                        },
                        "body": {
                            "type": "object",
                            "description": "Request body for POST/PUT"
                        }
                    },
                    "required": ["url", "method"]
                }
            }
        }


class MetaAgentBuilder:
    """Builder for creating meta agents that can create other agents."""
    
    def __init__(self, agent_manager: OpenAIAgentManager):
        self.agent_manager = agent_manager
    
    def create_meta_agent(self) -> str:
        """Create a meta agent that can design and create other agents."""
        meta_instructions = """You are a Meta Agent Designer. Your role is to help users create specialized AI agents for their needs.

When a user describes what they want an agent to do, you should:

1. Understand the requirements and ask clarifying questions if needed
2. Design the agent's personality, capabilities, and constraints
3. Generate detailed instructions for the agent
4. Recommend appropriate tools the agent should have access to
5. Suggest the optimal model and parameters

You should output a structured agent configuration that includes:
- Name: A descriptive name for the agent
- Instructions: Detailed system instructions
- Tools: List of tools the agent needs
- Model: The recommended model (e.g., gpt-4-turbo-preview)
- Temperature: Creativity level (0-1)
- Metadata: Any additional context or tags

Be creative but practical. Ensure agents are helpful, harmless, and honest."""

        config = AgentConfig(
            name="Meta Agent Designer",
            instructions=meta_instructions,
            model="gpt-4-turbo-preview",
            temperature=0.8,
            tools=[
                {"type": "code_interpreter"},
                self.agent_manager.create_function_tool(
                    name="create_agent",
                    description="Create a new AI agent with specified configuration",
                    parameters={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "instructions": {"type": "string"},
                            "tools": {"type": "array", "items": {"type": "object"}},
                            "model": {"type": "string"},
                            "temperature": {"type": "number"}
                        },
                        "required": ["name", "instructions"]
                    }
                )
            ]
        )
        
        return self.agent_manager.create_agent(config)


# Export schemas for API integration
class AgentCreateRequest(BaseModel):
    """Request schema for creating an agent via API."""
    name: str
    instructions: str
    model: str = "gpt-4-turbo-preview"
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    temperature: float = Field(default=0.7, ge=0, le=2)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ThreadCreateRequest(BaseModel):
    """Request schema for creating a thread."""
    messages: List[Dict[str, str]] = Field(default_factory=list)


class MessageCreateRequest(BaseModel):
    """Request schema for adding a message to a thread."""
    content: str
    role: str = "user"


class RunAgentRequest(BaseModel):
    """Request schema for running an agent."""
    agent_id: str
    thread_id: str
    additional_instructions: Optional[str] = None