"""Custom exceptions and error handlers for the API."""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


class AgentPlatformError(Exception):
    """Base exception for the agent platform."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AgentNotFoundError(AgentPlatformError):
    """Raised when an agent is not found."""
    def __init__(self, agent_id: str):
        super().__init__(f"Agent with ID '{agent_id}' not found", 404)


class SessionNotFoundError(AgentPlatformError):
    """Raised when a session is not found."""
    def __init__(self, session_id: str):
        super().__init__(f"Session with ID '{session_id}' not found", 404)


class InvalidAgentConfigError(AgentPlatformError):
    """Raised when agent configuration is invalid."""
    def __init__(self, message: str):
        super().__init__(f"Invalid agent configuration: {message}", 400)


class AuthenticationError(AgentPlatformError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)


class AuthorizationError(AgentPlatformError):
    """Raised when authorization fails."""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, 403)


class OpenAIAPIError(AgentPlatformError):
    """Raised when OpenAI API calls fail."""
    def __init__(self, message: str):
        super().__init__(f"OpenAI API error: {message}", 503)


async def agent_platform_exception_handler(request: Request, exc: AgentPlatformError):
    """Handle custom platform exceptions."""
    logger.error(f"Platform error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code
        }
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception("Unexpected error occurred")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later.",
            "status_code": 500
        }
    )