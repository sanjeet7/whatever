"""Middleware for the API."""

import time
import logging
from typing import Dict, Callable
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs all incoming requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate process time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} for {request.method} {request.url.path} "
            f"(took {process_time:.3f}s)"
        )
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = timedelta(seconds=period)
        self.clients: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not request.client:
            return await call_next(request)
        
        client_id = request.client.host
        now = datetime.now()
        
        # Clean old entries
        self.clients[client_id] = [
            timestamp for timestamp in self.clients[client_id]
            if now - timestamp < self.period
        ]
        
        # Check rate limit
        if len(self.clients[client_id]) >= self.calls:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RateLimitExceeded",
                    "message": f"Rate limit exceeded. Maximum {self.calls} requests per {self.period.seconds} seconds."
                }
            )
        
        # Record this request
        self.clients[client_id].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(self.calls - len(self.clients[client_id]))
        response.headers["X-RateLimit-Reset"] = str(int((now + self.period).timestamp()))
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response