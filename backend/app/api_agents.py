"""FastAPI application using the official OpenAI Agents SDK."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import uuid

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from .agents_sdk import (
    AgentManager, HandoffAgentSystem,
    AgentResponse, RunResponse
)
from .validators import (
    ValidatedAgentCreateRequest, ValidatedAgentRunRequest, 
    ValidatedMetaAgentDesignRequest, ValidatedChatMessage
)
from .exceptions import (
    AgentPlatformError, AgentNotFoundError, SessionNotFoundError,
    InvalidAgentConfigError, OpenAIAPIError,
    agent_platform_exception_handler, validation_exception_handler,
    generic_exception_handler
)
from .auth import get_current_active_user, Token, UserCreate, UserResponse, create_access_token
from .registry import RegistryService
from .database import Database
from .middleware import RequestLoggingMiddleware, RateLimitingMiddleware, SecurityHeadersMiddleware
from .orchestration import OrchestrationEngine
import logging
from pydantic import ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentPlatformAPI:
    """API for the Agent Platform using OpenAI Agents SDK."""
    
    def __init__(self):
        self.db = Database()
        self.registry = RegistryService(self.db)
        self.agent_manager = AgentManager()
        self.handoff_system = HandoffAgentSystem()
        self.orchestrator = OrchestrationEngine(registry=self.registry)
        self.api = self._create_api()
        self._websocket_connections: Dict[str, WebSocket] = {}
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def _create_api(self) -> FastAPI:
        """Create the FastAPI application."""
        app = FastAPI(
            title="AI Agent Platform - OpenAI Agents SDK",
            version="2.0.0",
            description="Modern AI Agent Platform powered by the official OpenAI Agents SDK"
        )
        
        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add middleware
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RateLimitingMiddleware, calls=100, period=60)
        app.add_middleware(RequestLoggingMiddleware)
        
        # Add exception handlers
        app.add_exception_handler(AgentPlatformError, agent_platform_exception_handler)
        app.add_exception_handler(ValidationError, validation_exception_handler)
        app.add_exception_handler(Exception, generic_exception_handler)
        
        # Dependency providers
        def get_agent_manager() -> AgentManager:
            return self.agent_manager
        
        def get_registry() -> RegistryService:
            return self.registry
        
        def get_handoff_system() -> HandoffAgentSystem:
            return self.handoff_system
        
        # Health check
        @app.get("/health")
        def health() -> Dict[str, str]:
            return {
                "status": "healthy",
                "version": "2.0.0",
                "sdk": "openai-agents"
            }
        
        # Authentication endpoints
        @app.post("/auth/register", response_model=UserResponse)
        async def register(user: UserCreate) -> Dict[str, Any]:
            """Register a new user."""
            # Simplified for demo - in production, save to database
            return {
                "id": 1,
                "username": user.username,
                "email": user.email,
                "is_active": True,
                "is_superuser": False,
                "created_at": datetime.utcnow()
            }
        
        @app.post("/auth/token", response_model=Token)
        async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
            """Login and get access token."""
            # Simplified for demo - in production, verify password against database
            access_token = create_access_token(data={"sub": form_data.username})
            return {"access_token": access_token, "token_type": "bearer"}
        
        # Meta Agent endpoints
        @app.post("/meta-agent/design")
        async def design_agent(
            request: ValidatedMetaAgentDesignRequest,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: AgentManager = Depends(get_agent_manager)
        ) -> Dict[str, Any]:
            """Use the meta agent to design a new agent based on requirements."""
            try:
                logger.info(f"User {current_user['username']} designing agent with requirements")
                # Use async meta design to avoid thread event loop issues
                result = await agent_manager.design_agent_with_meta_async(request.requirements)
                
                # Save the design to registry
                self.registry.create_agent_template(
                    name=result["suggested_config"]["name"],
                    description=request.requirements,
                    instructions_template=result["suggested_config"]["instructions"],
                    model_config={"model": result["suggested_config"]["model"]},
                    created_by=current_user["username"]
                )
                
                return {
                    "status": "success",
                    "design": result["design"],
                    "suggested_config": result["suggested_config"]
                }
            except Exception as e:
                logger.error(f"Error designing agent: {str(e)}")
                raise OpenAIAPIError(str(e))
        
        # Agent management endpoints
        @app.post("/agents", response_model=Dict[str, Any])
        async def create_agent(
            request: ValidatedAgentCreateRequest,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: AgentManager = Depends(get_agent_manager)
        ) -> Dict[str, Any]:
            """Create a new AI agent."""
            try:
                logger.info(f"User {current_user['username']} creating agent: {request.name}")
                
                config = {
                    "name": request.name,
                    "instructions": request.instructions,
                    "model": request.model,
                    "tools": request.tools,
                    "metadata": {**request.metadata, "owner": current_user["username"]}
                }
                
                agent_id = agent_manager.create_agent(config)
                
                # Save to registry for persistence
                template = self.registry.create_agent_template(
                    name=request.name,
                    description=request.instructions[:200],
                    instructions_template=request.instructions,
                    model_config={"model": request.model},
                    created_by=current_user["username"]
                )
                
                logger.info(f"Agent created successfully: {agent_id}")
                
                return {
                    "agent_id": agent_id,
                    "template_id": template.id,
                    "name": request.name,
                    "status": "created"
                }
            except Exception as e:
                logger.error(f"Error creating agent: {str(e)}")
                raise InvalidAgentConfigError(str(e))
        
        @app.get("/agents", response_model=List[AgentResponse])
        async def list_agents(
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: AgentManager = Depends(get_agent_manager)
        ) -> List[AgentResponse]:
            """List all available agents."""
            agents = agent_manager.list_agents()
            # Always expose orchestrator as primary entrypoint
            orchestrator_entry = {
                "id": "orchestrator",
                "name": "Orchestrator",
                "model": "router",
                "tools": [],
            }
            combined = [orchestrator_entry] + agents
            return [AgentResponse(**agent) for agent in combined]
        
        @app.get("/agents/{agent_id}", response_model=AgentResponse)
        async def get_agent(
            agent_id: str,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: AgentManager = Depends(get_agent_manager)
        ) -> AgentResponse:
            """Get details of a specific agent."""
            agent = agent_manager.get_agent(agent_id)
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            return AgentResponse(
                id=agent_id,
                name=agent.name,
                model=agent.model,
                tools=[getattr(tool, 'name', tool.__class__.__name__) for tool in agent.tools] if agent.tools else []
            )
        
        # Agent execution endpoints
        @app.post("/agents/run", response_model=RunResponse)
        async def run_agent(
            request: ValidatedAgentRunRequest,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: AgentManager = Depends(get_agent_manager)
        ) -> RunResponse:
            """Run an agent with user input."""
            try:
                logger.info(f"User {current_user['username']} running agent {request.agent_id}")
                
                output = await agent_manager.run_agent_async(
                    request.agent_id,
                    request.user_input
                )
                
                return RunResponse(
                    agent_id=request.agent_id,
                    output=output
                )
            except ValueError as e:
                logger.error(f"Agent not found: {request.agent_id}")
                raise AgentNotFoundError(request.agent_id)
            except Exception as e:
                logger.error(f"Error running agent: {str(e)}")
                raise OpenAIAPIError(str(e))
        
        # Handoff system endpoint
        @app.post("/handoff/triage")
        async def triage_request(
            request: Dict[str, str],
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            handoff_system: HandoffAgentSystem = Depends(get_handoff_system)
        ) -> Dict[str, Any]:
            """Route a request through the handoff triage system."""
            try:
                user_input = request.get("input", "")
                # Prefer async path to avoid blocking
                output = await handoff_system.handle_request_async(user_input)
                
                return {
                    "status": "success",
                    "output": output,
                    "system": "handoff_triage"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Session management for conversations
        @app.post("/sessions/create")
        async def create_session(
            current_user: Dict[str, Any] = Depends(get_current_active_user)
        ) -> Dict[str, str]:
            """Create a new conversation session (persisted)."""
            session_id = f"sess_{uuid.uuid4().hex}"
            self.registry.create_chat_session(session_id=session_id, user=current_user["username"])
            return {"session_id": session_id}
        
        @app.get("/sessions/{session_id}")
        async def get_session(
            session_id: str,
            current_user: Dict[str, Any] = Depends(get_current_active_user)
        ) -> Dict[str, Any]:
            """Get session details with persisted messages."""
            session = self.registry.get_chat_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            messages = self.registry.list_chat_messages(session_id)
            return {
                "session_id": session.session_id,
                "user": session.user,
                "created_at": session.created_at.isoformat(),
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content,
                        "timestamp": m.created_at.isoformat(),
                        "agent_id": m.agent_id,
                    }
                    for m in messages
                ],
            }
        
        # WebSocket for real-time agent interactions
        @app.websocket("/ws/{session_id}")
        async def websocket_endpoint(
            websocket: WebSocket,
            session_id: str
        ):
            """WebSocket endpoint for real-time agent interactions."""
            await websocket.accept()
            self._websocket_connections[session_id] = websocket
            
            try:
                while True:
                    data = await websocket.receive_json()
                    
                    try:
                        # Validate the message
                        validated_msg = ValidatedChatMessage(**data)
                        
                        if validated_msg.type == "chat":
                            agent_id = validated_msg.agent_id
                            message = validated_msg.message
                            
                            logger.info(f"WebSocket chat from session {session_id} to agent {agent_id}")
                            
                            # Persist user message
                            self.registry.append_chat_message(
                                session_id=session_id,
                                role="user",
                                content=message,
                                agent_id=None,
                            )
                            
                            # Orchestrate
                            try:
                                if agent_id == "orchestrator":
                                    # Route via orchestrator (sync wrapper in thread)
                                    loop = asyncio.get_running_loop()
                                    result = await loop.run_in_executor(
                                        None,
                                        lambda: self.orchestrator.route_request(user_input=message),
                                    )
                                    output = result.response
                                    responding_agent_id = "orchestrator"
                                else:
                                    output = await self.agent_manager.run_agent_async(agent_id, message)
                                    responding_agent_id = agent_id
                                
                                # Persist assistant response
                                self.registry.append_chat_message(
                                    session_id=session_id,
                                    role="assistant",
                                    content=output,
                                    agent_id=responding_agent_id,
                                )
                                
                                # Send response back
                                await websocket.send_json({
                                    "type": "response",
                                    "agent_id": responding_agent_id,
                                    "message": output,
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                                
                            except ValueError:
                                logger.error(f"Agent not found: {agent_id}")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": f"Agent '{agent_id}' not found"
                                })
                            except Exception as e:
                                logger.error(f"Error in WebSocket chat: {str(e)}")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "An error occurred processing your message"
                                })
                        
                        elif validated_msg.type == "ping":
                            await websocket.send_json({"type": "pong"})
                            
                    except ValidationError as e:
                        logger.warning(f"Invalid WebSocket message: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid message format",
                            "details": e.errors()
                        })
                    
            except WebSocketDisconnect:
                del self._websocket_connections[session_id]
        
        # Tool information endpoint
        @app.get("/tools/available")
        async def get_available_tools(
            current_user: Dict[str, Any] = Depends(get_current_active_user)
        ) -> List[Dict[str, str]]:
            """Get available tool definitions."""
            return [
                {"name": "web_search", "description": "Search the web for information"},
                {"name": "code_analysis", "description": "Analyze code for improvements"},
                {"name": "content_generation", "description": "Generate various types of content"},
                {"name": "data_access", "description": "Query databases"},
                {"name": "create_agent_config", "description": "Create agent configurations"}
            ]
        
        # Analytics endpoint
        @app.get("/analytics/usage")
        async def get_usage_analytics(
            current_user: Dict[str, Any] = Depends(get_current_active_user)
        ) -> Dict[str, Any]:
            """Get usage analytics."""
            # In production, this would query real analytics data
            return {
                "total_agents": len(self.agent_manager.agents),
                "total_sessions": len(self._active_sessions),
                "active_connections": len(self._websocket_connections),
                "user_sessions": len([s for s in self._active_sessions.values() 
                                    if s["user"] == current_user["username"]])
            }
        
        return app


# Create application instance
agent_platform = AgentPlatformAPI()
app = agent_platform.api

__all__ = ["AgentPlatformAPI", "app", "agent_platform"]