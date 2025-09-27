"""FastAPI application using the official OpenAI Agents SDK."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .agents_sdk import (
    AgentManager, HandoffAgentSystem,
    AgentCreateRequest, AgentRunRequest, MetaAgentDesignRequest,
    AgentResponse, RunResponse
)
from .auth import get_current_active_user, Token, UserCreate, UserResponse, create_access_token
from .registry import RegistryService
from .database import Database


class AgentPlatformAPI:
    """API for the Agent Platform using OpenAI Agents SDK."""
    
    def __init__(self):
        self.db = Database()
        self.registry = RegistryService(self.db)
        self.agent_manager = AgentManager()
        self.handoff_system = HandoffAgentSystem()
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
        async def login(username: str, password: str) -> Dict[str, str]:
            """Login and get access token."""
            # Simplified for demo
            access_token = create_access_token(data={"sub": username})
            return {"access_token": access_token, "token_type": "bearer"}
        
        # Meta Agent endpoints
        @app.post("/meta-agent/design")
        async def design_agent(
            request: MetaAgentDesignRequest,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: AgentManager = Depends(get_agent_manager)
        ) -> Dict[str, Any]:
            """Use the meta agent to design a new agent based on requirements."""
            try:
                result = agent_manager.design_agent_with_meta(request.requirements)
                
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
                raise HTTPException(status_code=500, detail=str(e))
        
        # Agent management endpoints
        @app.post("/agents", response_model=Dict[str, Any])
        async def create_agent(
            request: AgentCreateRequest,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: AgentManager = Depends(get_agent_manager)
        ) -> Dict[str, Any]:
            """Create a new AI agent."""
            try:
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
                
                return {
                    "agent_id": agent_id,
                    "template_id": template.id,
                    "name": request.name,
                    "status": "created"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/agents", response_model=List[AgentResponse])
        async def list_agents(
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: AgentManager = Depends(get_agent_manager)
        ) -> List[AgentResponse]:
            """List all available agents."""
            agents = agent_manager.list_agents()
            return [AgentResponse(**agent) for agent in agents]
        
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
                tools=[tool.__name__ for tool in agent.tools] if agent.tools else []
            )
        
        # Agent execution endpoints
        @app.post("/agents/run", response_model=RunResponse)
        async def run_agent(
            request: AgentRunRequest,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: AgentManager = Depends(get_agent_manager)
        ) -> RunResponse:
            """Run an agent with user input."""
            try:
                output = await agent_manager.run_agent_async(
                    request.agent_id,
                    request.user_input
                )
                
                return RunResponse(
                    agent_id=request.agent_id,
                    output=output
                )
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
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
                output = handoff_system.handle_request(user_input)
                
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
            """Create a new conversation session."""
            session_id = f"session_{current_user['username']}_{datetime.utcnow().timestamp()}"
            self._active_sessions[session_id] = {
                "user": current_user["username"],
                "created_at": datetime.utcnow(),
                "messages": []
            }
            return {"session_id": session_id}
        
        @app.get("/sessions/{session_id}")
        async def get_session(
            session_id: str,
            current_user: Dict[str, Any] = Depends(get_current_active_user)
        ) -> Dict[str, Any]:
            """Get session details."""
            session = self._active_sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            if session["user"] != current_user["username"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            return session
        
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
                    
                    if data["type"] == "chat":
                        agent_id = data.get("agent_id", "triage_agent")
                        message = data.get("message", "")
                        
                        # Store message in session
                        if session_id in self._active_sessions:
                            self._active_sessions[session_id]["messages"].append({
                                "role": "user",
                                "content": message,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        
                        # Run the appropriate system
                        try:
                            if agent_id == "triage_agent":
                                output = self.handoff_system.handle_request(message)
                            else:
                                output = await self.agent_manager.run_agent_async(agent_id, message)
                            
                            # Store response in session
                            if session_id in self._active_sessions:
                                self._active_sessions[session_id]["messages"].append({
                                    "role": "assistant",
                                    "content": output,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "agent_id": agent_id
                                })
                            
                            # Send response back
                            await websocket.send_json({
                                "type": "response",
                                "agent_id": agent_id,
                                "message": output,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                            
                        except Exception as e:
                            await websocket.send_json({
                                "type": "error",
                                "message": str(e)
                            })
                    
                    elif data["type"] == "ping":
                        await websocket.send_json({"type": "pong"})
                    
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