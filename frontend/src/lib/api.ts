import axios from 'axios'

const API_BASE_URL = '/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: async (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },
  
  register: async (data: { username: string; email: string; password: string }) => {
    const response = await api.post('/auth/register', data)
    return response.data
  },
}

// Agents API
export const agentsAPI = {
  list: async () => {
    const response = await api.get('/agents')
    return response.data
  },
  
  create: async (data: {
    name: string
    instructions: string
    model?: string
    tools?: string[]
  }) => {
    const response = await api.post('/agents', data)
    return response.data
  },
  
  get: async (agentId: string) => {
    const response = await api.get(`/agents/${agentId}`)
    return response.data
  },
  
  run: async (agentId: string, userInput: string) => {
    const response = await api.post('/agents/run', {
      agent_id: agentId,
      user_input: userInput,
    })
    return response.data
  },
}

// Meta Agent API
export const metaAgentAPI = {
  design: async (requirements: string) => {
    const response = await api.post('/meta-agent/design', { requirements })
    return response.data
  },
}

// Sessions API
export const sessionsAPI = {
  create: async () => {
    const response = await api.post('/sessions/create')
    return response.data
  },
  
  get: async (sessionId: string) => {
    const response = await api.get(`/sessions/${sessionId}`)
    return response.data
  },
}

// Tools API
export const toolsAPI = {
  list: async () => {
    const response = await api.get('/tools/available')
    return response.data
  },
}

// Analytics API
export const analyticsAPI = {
  getUsage: async () => {
    const response = await api.get('/analytics/usage')
    return response.data
  },
}

// WebSocket connection
export const createWebSocket = (sessionId: string) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws/${sessionId}`)
  return ws
}