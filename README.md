# AI Agent Platform

A modern, full-stack AI agent platform built with the official OpenAI Agents SDK, FastAPI, and React.

## Features

### 🤖 Pre-built Agents
- **Meta Agent Designer**: AI-powered agent creation assistant
- **Triage Agent**: Routes requests to appropriate specialized agents
- **Customer Support Agent**: Handles support inquiries and refunds
- **Code Assistant**: Helps with code reviews and debugging
- **Content Creator**: Generates various types of content

### 🔄 Agent Handoffs
Seamless transitions between specialized agents for complex workflows

### 💬 Real-time Chat
WebSocket-powered instant messaging with agent responses

### 🛠️ Modern Tech Stack
- **Backend**: FastAPI, OpenAI Agents SDK, SQLite, WebSockets
- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **Authentication**: JWT-based auth system

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API Key

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Add your OpenAI API key to `.env`:
```
OPENAI_API_KEY=your-api-key-here
```

6. Run the backend:
```bash
python -m app.main
```

The backend will be available at http://localhost:8000

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Install Tailwind CSS animation plugin:
```bash
npm install tailwindcss-animate
```

4. Run the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Usage

1. **Register/Login**: Create an account or login at http://localhost:3000/login

2. **Design an Agent**: Use the Meta Agent Designer to create custom agents based on your requirements

3. **Chat with Agents**: Select an agent and start a real-time conversation

4. **Monitor Usage**: View analytics and platform statistics on the dashboard

## API Documentation

Once the backend is running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

### Backend Structure
```
backend/
├── app/
│   ├── agents_sdk.py      # OpenAI Agents SDK integration
│   ├── api_agents.py      # FastAPI application
│   ├── auth.py            # Authentication system
│   ├── database.py        # SQLite database
│   ├── models.py          # Data models
│   └── registry.py        # Agent registry service
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/        # Reusable UI components
│   ├── contexts/          # React contexts (auth)
│   ├── pages/             # Page components
│   ├── lib/               # API client and utilities
│   └── types/             # TypeScript types
```

## Key Features Implementation

### Meta Agent Designer
The Meta Agent uses the OpenAI Agents SDK to analyze requirements and generate agent configurations:
- Natural language requirement input
- AI-powered agent design suggestions
- Automatic tool selection based on capabilities

### Agent Handoffs
Triage agent can seamlessly transfer conversations to specialized agents:
- Shopping inquiries → Shopping Assistant
- Support issues → Support Agent
- Maintains conversation context

### Real-time Communication
WebSocket implementation for instant messaging:
- Persistent connections
- Real-time agent responses
- Session management

## Development

### Adding New Agents

1. Define the agent in `backend/app/agents_sdk.py`:
```python
self.new_agent = Agent(
    name="New Agent",
    instructions="Agent instructions...",
    tools=[...],
    model="gpt-4-turbo-preview"
)
```

2. Add to the agent registry in `AgentManager.__init__`

### Adding New Tools

1. Create a function tool in `backend/app/agents_sdk.py`:
```python
@function_tool
def new_tool(param: str) -> str:
    """Tool description"""
    return "Tool result"
```

2. Register in the tool registry

## Deployment

### Docker (Coming Soon)
Docker configuration is planned for easy deployment.

### Production Considerations
- Use a production database (PostgreSQL recommended)
- Set secure SECRET_KEY for JWT
- Enable HTTPS
- Configure CORS for your domain
- Use environment variables for sensitive data

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.