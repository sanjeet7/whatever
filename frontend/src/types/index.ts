export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export interface Agent {
  id: string
  name: string
  model: string
  tools: string[]
}

export interface AgentConfig {
  name: string
  instructions: string
  model: string
  tools: string[]
}

export interface Message {
  id?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  agent_id?: string
}

export interface Session {
  session_id: string
  user: string
  created_at: string
  messages: Message[]
}

export interface Tool {
  name: string
  description: string
}

export interface AnalyticsData {
  total_agents: number
  total_sessions: number
  active_connections: number
  user_sessions: number
}