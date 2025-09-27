"""HTTP API surface for the dynamic agent platform backend."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .dynamic import DynamicBuilder
from .orchestration import OrchestrationEngine, RouteResult
from .registry import RegistryService
from .schemas import (
    AgentDeployRequest,
    AgentDeployResponse,
    AgentRead,
    RouteRequest,
    RouteResponse,
    SelfImproveResponse,
    TemplateCreate,
    TemplateRead,
    ToolCreate,
    ToolRead,
    FunctionCreate,
    FunctionRead,
)


class Application:
    """Container for shared services and the FastAPI instance."""

    def __init__(self, registry: RegistryService | None = None) -> None:
        self.registry = registry or RegistryService()
        self.builder = DynamicBuilder(registry=self.registry)
        self.engine = OrchestrationEngine(registry=self.registry, builder=self.builder)
        self.api = self._create_api()

    # ------------------------------------------------------------------
    # Service layer helpers (used by tests and CLI tooling)
    # ------------------------------------------------------------------
    def create_template(self, **kwargs: Any):
        return self.registry.create_agent_template(**kwargs)

    def list_templates(self):
        return self.registry.list_agent_templates()

    def create_tool(self, **kwargs: Any):
        return self.registry.create_tool(**kwargs)

    def list_tools(self):
        return self.registry.list_tools()

    def create_function(self, **kwargs: Any):
        return self.registry.create_function(**kwargs)

    def list_functions(self):
        return self.registry.list_functions()

    def list_agents(self, owner_id: str | None = None):
        return self.registry.list_agent_instances(owner_id=owner_id)

    def deploy_agent(self, **kwargs: Any) -> int:
        return self.engine.deploy_agent(**kwargs)

    def route_request(self, *, user_input: str, owner_id: str | None = None) -> RouteResult:
        return self.engine.route_request(user_input=user_input, owner_id=owner_id)

    async def self_improve(self, owner_id: str | None = None) -> dict[str, Any]:
        return await self.engine.self_improve(owner_id=owner_id)

    # ------------------------------------------------------------------
    # FastAPI setup
    # ------------------------------------------------------------------
    def _create_api(self) -> FastAPI:
        app = FastAPI(title="Dynamic Agent Platform", version="0.1.0")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        def get_registry() -> RegistryService:
            return self.registry

        def get_engine() -> OrchestrationEngine:
            return self.engine

        @app.get("/health")
        def health() -> dict[str, str]:
            return {"status": "ok"}

        @app.post("/templates", response_model=TemplateRead, status_code=201)
        def create_template_endpoint(
            payload: TemplateCreate,
            registry: RegistryService = Depends(get_registry),
        ) -> TemplateRead:
            template = registry.create_agent_template(**payload.model_dump())
            return TemplateRead.model_validate(template)

        @app.get("/templates", response_model=list[TemplateRead])
        def list_templates_endpoint(
            registry: RegistryService = Depends(get_registry),
        ) -> list[TemplateRead]:
            return [TemplateRead.model_validate(item) for item in registry.list_agent_templates()]

        @app.post("/tools", response_model=ToolRead, status_code=201)
        def create_tool_endpoint(
            payload: ToolCreate,
            registry: RegistryService = Depends(get_registry),
        ) -> ToolRead:
            tool = registry.create_tool(**payload.model_dump())
            return ToolRead.model_validate(tool)

        @app.get("/tools", response_model=list[ToolRead])
        def list_tools_endpoint(
            registry: RegistryService = Depends(get_registry),
        ) -> list[ToolRead]:
            return [ToolRead.model_validate(item) for item in registry.list_tools()]

        @app.post("/functions", response_model=FunctionRead, status_code=201)
        def create_function_endpoint(
            payload: FunctionCreate,
            registry: RegistryService = Depends(get_registry),
        ) -> FunctionRead:
            function = registry.create_function(**payload.model_dump())
            return FunctionRead.model_validate(function)

        @app.get("/functions", response_model=list[FunctionRead])
        def list_functions_endpoint(
            registry: RegistryService = Depends(get_registry),
        ) -> list[FunctionRead]:
            return [FunctionRead.model_validate(item) for item in registry.list_functions()]

        @app.get("/agents", response_model=list[AgentRead])
        def list_agents_endpoint(
            owner_id: str | None = None,
            registry: RegistryService = Depends(get_registry),
        ) -> list[AgentRead]:
            agents = registry.list_agent_instances(owner_id=owner_id)
            return [AgentRead.model_validate(agent) for agent in agents]

        @app.post("/agents/deploy", response_model=AgentDeployResponse, status_code=201)
        def deploy_agent_endpoint(
            payload: AgentDeployRequest,
            registry: RegistryService = Depends(get_registry),
            engine: OrchestrationEngine = Depends(get_engine),
        ) -> AgentDeployResponse:
            instance_id = engine.deploy_agent(**payload.model_dump())
            instance = registry.get_agent_instance(instance_id)
            if instance is None:  # pragma: no cover - defensive guard
                raise HTTPException(status_code=500, detail="Agent deployment failed")
            return AgentDeployResponse.model_validate(instance)

        @app.post("/route", response_model=RouteResponse)
        def route_endpoint(
            payload: RouteRequest,
            engine: OrchestrationEngine = Depends(get_engine),
        ) -> RouteResponse:
            try:
                result = engine.route_request(
                    user_input=payload.user_input,
                    owner_id=payload.owner_id,
                )
            except ValueError as exc:  # no available agent
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            return RouteResponse.model_validate(result)

        @app.post("/self-improve", response_model=SelfImproveResponse)
        async def self_improve_endpoint(
            owner_id: str | None = None,
            engine: OrchestrationEngine = Depends(get_engine),
        ) -> SelfImproveResponse:
            result = await engine.self_improve(owner_id=owner_id)
            return SelfImproveResponse.model_validate(result)

        return app


application = Application()
app = application.api

__all__ = ["Application", "app", "application"]
