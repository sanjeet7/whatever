"""Enhanced API with OpenAI Agents SDK integration."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .openai_agents import (
    OpenAIAgentManager, AgentConfig, MetaAgentBuilder,
    AgentCreateRequest, ThreadCreateRequest, MessageCreateRequest, RunAgentRequest,
    ToolBuilder
)
from .auth import get_current_active_user, Token, UserCreate, UserResponse
from .registry import RegistryService
from .database import Database
from .schemas import SelfImproveResponse


class EnhancedApplication:
    """Enhanced application with OpenAI Agents integration."""
    
    def __init__(self):
        self.db = Database()
        self.registry = RegistryService(self.db)
        self.agent_manager = OpenAIAgentManager()
        self.meta_builder = MetaAgentBuilder(self.agent_manager)
        self.api = self._create_api()
        self._websocket_connections: Dict[str, WebSocket] = {}
        
        # Create meta agent on startup
        self._meta_agent_id = None
    
    def _create_api(self) -> FastAPI:
        """Create the FastAPI application."""
        app = FastAPI(
            title="AI Agent Platform",
            version="2.0.0",
            description="Modern AI Agent Platform powered by OpenAI Agents SDK"
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
        def get_agent_manager() -> OpenAIAgentManager:
            return self.agent_manager
        
        def get_registry() -> RegistryService:
            return self.registry
        
        # Health check
        @app.get("/health")
        def health() -> Dict[str, str]:
            return {"status": "healthy", "version": "2.0.0"}
        
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
            from .auth import create_access_token
            access_token = create_access_token(data={"sub": username})
            return {"access_token": access_token, "token_type": "bearer"}
        
        # Meta Agent endpoints
        @app.post("/meta-agent/create")
        async def create_meta_agent(
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: OpenAIAgentManager = Depends(get_agent_manager)
        ) -> Dict[str, Any]:
            """Create the meta agent for designing other agents."""
            if not self._meta_agent_id:
                self._meta_agent_id = self.meta_builder.create_meta_agent()
            return {
                "meta_agent_id": self._meta_agent_id,
                "status": "created",
                "message": "Meta agent is ready to help you design custom agents"
            }
        
        @app.post("/meta-agent/design")
        async def design_agent_with_meta(
            request: Dict[str, str],
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: OpenAIAgentManager = Depends(get_agent_manager)
        ) -> Dict[str, Any]:
            """Use meta agent to design a new agent based on requirements."""
            if not self._meta_agent_id:
                self._meta_agent_id = self.meta_builder.create_meta_agent()
            
            # Create thread and run meta agent
            thread_id = agent_manager.create_thread()
            agent_manager.add_message(
                thread_id, 
                f"Please design an AI agent with the following requirements: {request.get('requirements', '')}"
            )
            
            run = agent_manager.run_agent(self._meta_agent_id, thread_id)
            messages = agent_manager.get_messages(thread_id)
            
            # Extract the agent design from the response
            latest_message = messages[0] if messages else None
            
            return {
                "thread_id": thread_id,
                "run_id": run.id,
                "status": run.status,
                "design": latest_message.content[0].text.value if latest_message else None
            }
        
        # Agent management endpoints
        @app.post("/agents", response_model=Dict[str, Any])
        async def create_agent(
            request: AgentCreateRequest,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: OpenAIAgentManager = Depends(get_agent_manager),
            registry: RegistryService = Depends(get_registry)
        ) -> Dict[str, Any]:
            """Create a new AI agent."""
            config = AgentConfig(
                name=request.name,
                instructions=request.instructions,
                model=request.model,
                tools=request.tools,
                temperature=request.temperature,
                metadata={**request.metadata, "owner": current_user["username"]}
            )
            
            agent_id = agent_manager.create_agent(config)
            
            # Also save to our registry for persistence
            template = registry.create_agent_template(
                name=request.name,
                description=request.instructions[:200],  # First 200 chars as description
                instructions_template=request.instructions,
                model_config={"model": request.model, "temperature": request.temperature},
                created_by=current_user["username"]
            )
            
            return {
                "agent_id": agent_id,
                "template_id": template.id,
                "name": request.name,
                "status": "created"
            }
        
        @app.get("/agents")
        async def list_agents(
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: OpenAIAgentManager = Depends(get_agent_manager)
        ) -> List[Dict[str, Any]]:
            """List all agents."""
            agents = agent_manager.list_agents()
            return [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "model": agent.model,
                    "created_at": agent.created_at,
                    "metadata": agent.metadata
                }
                for agent in agents
            ]
        
        @app.delete("/agents/{agent_id}")
        async def delete_agent(
            agent_id: str,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: OpenAIAgentManager = Depends(get_agent_manager)
        ) -> Dict[str, Any]:
            """Delete an agent."""
            success = agent_manager.delete_agent(agent_id)
            if not success:
                raise HTTPException(status_code=404, detail="Agent not found")
            return {"status": "deleted", "agent_id": agent_id}
        
        # Thread management endpoints
        @app.post("/threads")
        async def create_thread(
            request: ThreadCreateRequest,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: OpenAIAgentManager = Depends(get_agent_manager)
        ) -> Dict[str, Any]:
            """Create a new conversation thread."""
            thread_id = agent_manager.create_thread(request.messages)
            return {"thread_id": thread_id, "status": "created"}
        
        @app.post("/threads/{thread_id}/messages")
        async def add_message(
            thread_id: str,
            request: MessageCreateRequest,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: OpenAIAgentManager = Depends(get_agent_manager)
        ) -> Dict[str, Any]:
            """Add a message to a thread."""
            message = agent_manager.add_message(thread_id, request.content, request.role)
            return {
                "message_id": message.id,
                "thread_id": thread_id,
                "status": "added"
            }
        
        @app.get("/threads/{thread_id}/messages")
        async def get_messages(
            thread_id: str,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: OpenAIAgentManager = Depends(get_agent_manager)
        ) -> List[Dict[str, Any]]:
            """Get all messages in a thread."""
            messages = agent_manager.get_messages(thread_id)
            return [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content[0].text.value if msg.content else "",
                    "created_at": msg.created_at
                }
                for msg in messages
            ]
        
        # Run agent endpoints
        @app.post("/run")
        async def run_agent(
            request: RunAgentRequest,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: OpenAIAgentManager = Depends(get_agent_manager)
        ) -> Dict[str, Any]:
            """Run an agent on a thread."""
            run = agent_manager.run_agent(
                request.agent_id,
                request.thread_id,
                request.additional_instructions
            )
            
            # Get the latest messages
            messages = agent_manager.get_messages(request.thread_id)
            latest_response = messages[0].content[0].text.value if messages else None
            
            return {
                "run_id": run.id,
                "thread_id": request.thread_id,
                "status": run.status,
                "response": latest_response
            }
        
        # WebSocket for real-time agent interactions
        @app.websocket("/ws/{client_id}")
        async def websocket_endpoint(
            websocket: WebSocket,
            client_id: str,
            agent_manager: OpenAIAgentManager = Depends(get_agent_manager)
        ):
            """WebSocket endpoint for real-time agent interactions."""
            await websocket.accept()
            self._websocket_connections[client_id] = websocket
            
            try:
                while True:
                    data = await websocket.receive_json()
                    
                    if data["type"] == "chat":
                        # Handle chat message
                        thread_id = data.get("thread_id")
                        agent_id = data.get("agent_id")
                        message = data.get("message")
                        
                        # Add message and run agent
                        agent_manager.add_message(thread_id, message)
                        run = agent_manager.run_agent(agent_id, thread_id)
                        
                        # Get response
                        messages = agent_manager.get_messages(thread_id)
                        latest_response = messages[0].content[0].text.value if messages else None
                        
                        # Send response back
                        await websocket.send_json({
                            "type": "response",
                            "thread_id": thread_id,
                            "message": latest_response,
                            "status": run.status
                        })
                    
            except WebSocketDisconnect:
                del self._websocket_connections[client_id]
        
        # Tool endpoints
        @app.get("/tools/available")
        async def get_available_tools(
            current_user: Dict[str, Any] = Depends(get_current_active_user)
        ) -> List[Dict[str, Any]]:
            """Get available tool definitions."""
            return [
                ToolBuilder.create_web_search_tool(),
                ToolBuilder.create_database_query_tool(),
                ToolBuilder.create_api_call_tool(),
                {"type": "code_interpreter"},
                {"type": "retrieval"}
            ]
        
        # Self-improvement endpoint
        @app.post("/self-improve")
        async def self_improve(
            agent_id: Optional[str] = None,
            current_user: Dict[str, Any] = Depends(get_current_active_user),
            agent_manager: OpenAIAgentManager = Depends(get_agent_manager)
        ) -> SelfImproveResponse:
            """Trigger self-improvement analysis."""
            # Create a specialized improvement agent
            improvement_config = AgentConfig(
                name="Self-Improvement Analyst",
                instructions="""Analyze the performance and capabilities of AI agents and suggest improvements.
                Consider: response quality, tool usage, efficiency, user satisfaction, and potential new features.""",
                model="gpt-4-turbo-preview",
                temperature=0.9
            )
            
            improvement_agent_id = agent_manager.create_agent(improvement_config)
            thread_id = agent_manager.create_thread()
            
            prompt = f"Analyze agent {agent_id} and suggest improvements" if agent_id else "Suggest general improvements for our AI agent platform"
            agent_manager.add_message(thread_id, prompt)
            
            run = agent_manager.run_agent(improvement_agent_id, thread_id)
            messages = agent_manager.get_messages(thread_id)
            
            suggestions = messages[0].content[0].text.value if messages else "No suggestions generated"
            
            # Clean up improvement agent
            agent_manager.delete_agent(improvement_agent_id)
            
            return SelfImproveResponse(
                proposals=[suggestions],
                generated={"agent_analyzed": agent_id or "platform"},
                validation={"status": "completed"}
            )
        
        return app


# Create application instance
enhanced_app = EnhancedApplication()
app_v2 = enhanced_app.api

__all__ = ["EnhancedApplication", "app_v2", "enhanced_app"]