"""CLI launcher for the enhanced backend API with OpenAI Agents SDK."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_requirements():
    """Check if required environment variables are set."""
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set in environment variables")
        print("Please copy .env.example to .env and add your OpenAI API key")
        sys.exit(1)


def main() -> None:
    """Run the enhanced API server."""
    check_requirements()
    
    # Import here to ensure env vars are loaded
    from .api_v2 import app_v2
    
    print("🚀 Starting AI Agent Platform v2.0")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("🔧 OpenAI Agents SDK: Enabled")
    print("🔐 Authentication: Enabled")
    print("🌐 WebSocket Support: Enabled")
    
    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    uvicorn.run(
        app_v2,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )


if __name__ == "__main__":
    main()
