"""Input validators for the API."""

import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field, validator


class AgentNameValidator:
    """Validates agent names."""
    
    @staticmethod
    def validate(name: str) -> str:
        if not name or not name.strip():
            raise ValueError("Agent name cannot be empty")
        
        if len(name) < 3:
            raise ValueError("Agent name must be at least 3 characters long")
        
        if len(name) > 50:
            raise ValueError("Agent name must not exceed 50 characters")
        
        # Allow letters, numbers, spaces, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
            raise ValueError("Agent name can only contain letters, numbers, spaces, hyphens, and underscores")
        
        return name.strip()


class InstructionsValidator:
    """Validates agent instructions."""
    
    @staticmethod
    def validate(instructions: str) -> str:
        if not instructions or not instructions.strip():
            raise ValueError("Instructions cannot be empty")
        
        if len(instructions) < 10:
            raise ValueError("Instructions must be at least 10 characters long")
        
        if len(instructions) > 5000:
            raise ValueError("Instructions must not exceed 5000 characters")
        
        return instructions.strip()


class ToolsValidator:
    """Validates tool selections."""
    
    VALID_TOOLS = ["web_search", "code_analysis", "content_generation", "data_access", "create_agent_config"]
    
    @staticmethod
    def validate(tools: List[str]) -> List[str]:
        if not isinstance(tools, list):
            raise ValueError("Tools must be a list")
        
        # Remove duplicates
        tools = list(set(tools))
        
        # Validate each tool
        invalid_tools = [tool for tool in tools if tool not in ToolsValidator.VALID_TOOLS]
        if invalid_tools:
            raise ValueError(f"Invalid tools: {', '.join(invalid_tools)}")
        
        # Limit number of tools
        if len(tools) > 5:
            raise ValueError("An agent can have a maximum of 5 tools")
        
        return tools


class ModelValidator:
    """Validates model selection."""
    
    VALID_MODELS = ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"]
    
    @staticmethod
    def validate(model: str) -> str:
        if model not in ModelValidator.VALID_MODELS:
            raise ValueError(f"Invalid model. Must be one of: {', '.join(ModelValidator.VALID_MODELS)}")
        return model


class RequirementsValidator:
    """Validates meta agent requirements."""
    
    @staticmethod
    def validate(requirements: str) -> str:
        if not requirements or not requirements.strip():
            raise ValueError("Requirements cannot be empty")
        
        if len(requirements) < 20:
            raise ValueError("Requirements must be at least 20 characters long to provide meaningful context")
        
        if len(requirements) > 2000:
            raise ValueError("Requirements must not exceed 2000 characters")
        
        return requirements.strip()


class MessageValidator:
    """Validates chat messages."""
    
    @staticmethod
    def validate(message: str) -> str:
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
        
        if len(message) > 2000:
            raise ValueError("Message must not exceed 2000 characters")
        
        return message.strip()


# Enhanced Pydantic models with validators
class ValidatedAgentCreateRequest(BaseModel):
    """Validated request for creating an agent."""
    name: str = Field(..., description="Agent name")
    instructions: str = Field(..., description="Agent instructions")
    model: str = Field(default="gpt-4-turbo-preview", description="Model to use")
    tools: List[str] = Field(default_factory=list, description="List of tools")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('name')
    def validate_name(cls, v):
        return AgentNameValidator.validate(v)
    
    @validator('instructions')
    def validate_instructions(cls, v):
        return InstructionsValidator.validate(v)
    
    @validator('model')
    def validate_model(cls, v):
        return ModelValidator.validate(v)
    
    @validator('tools')
    def validate_tools(cls, v):
        return ToolsValidator.validate(v)


class ValidatedMetaAgentDesignRequest(BaseModel):
    """Validated request for meta agent design."""
    requirements: str = Field(..., description="Agent requirements")
    
    @validator('requirements')
    def validate_requirements(cls, v):
        return RequirementsValidator.validate(v)


class ValidatedAgentRunRequest(BaseModel):
    """Validated request for running an agent."""
    agent_id: str = Field(..., description="Agent ID")
    user_input: str = Field(..., description="User input message")
    
    @validator('agent_id')
    def validate_agent_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Agent ID cannot be empty")
        return v.strip()
    
    @validator('user_input')
    def validate_user_input(cls, v):
        return MessageValidator.validate(v)


class ValidatedChatMessage(BaseModel):
    """Validated chat message."""
    type: str = Field(..., description="Message type")
    agent_id: str = Field(..., description="Agent ID")
    message: str = Field(..., description="Message content")
    
    @validator('type')
    def validate_type(cls, v):
        if v not in ["chat", "ping"]:
            raise ValueError("Invalid message type")
        return v
    
    @validator('message')
    def validate_message(cls, v):
        return MessageValidator.validate(v)