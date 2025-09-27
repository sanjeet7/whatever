import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { agentsAPI, sessionsAPI, createWebSocket } from '@/lib/api'
import type { Agent, Message } from '@/types'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'

export function ChatPage() {
  const { agentId = 'orchestrator' } = useParams()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const { data: agents = [] } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: agentsAPI.list,
  })

  const currentAgent = (agents as Agent[]).find((a: Agent) => a.id === agentId) || {
    id: 'orchestrator',
    name: 'Orchestrator',
    model: 'router',
    tools: [],
  }

  const createSessionMutation = useMutation({
    mutationFn: sessionsAPI.create,
    onSuccess: (data) => {
      localStorage.setItem('session_id', data.session_id)
      connectWebSocket(data.session_id)
    },
  })

  useEffect(() => {
    const existing = localStorage.getItem('session_id')
    if (existing) {
      // preload history
      sessionsAPI.get(existing).then((res) => {
        setMessages(res.messages || [])
        connectWebSocket(existing)
      }).catch(() => {
        // if failed (expired), create new
        createSessionMutation.mutate()
      })
    } else {
      createSessionMutation.mutate()
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const connectWebSocket = (sid: string) => {
    const ws = createWebSocket(sid)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      toast.success('Connected to chat')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'response') {
        setIsTyping(false)
        setMessages((prev: Message[]) => [...prev, {
          role: 'assistant',
          content: data.message,
          timestamp: data.timestamp,
          agent_id: data.agent_id,
        }])
      } else if (data.type === 'error') {
        setIsTyping(false)
        toast.error(data.message)
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      toast.error('Disconnected from chat')
    }

    ws.onerror = () => {
      toast.error('Connection error')
    }
  }

  const sendMessage = () => {
    if (!input.trim() || !wsRef.current || !isConnected) return

    const message: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev: Message[]) => [...prev, message])
    setInput('')
    setIsTyping(true)

    wsRef.current.send(JSON.stringify({
      type: 'chat',
      agent_id: agentId,
      message: input,
    }))
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex h-full">
      {/* Sidebar with agent selection */}
      <div className="w-64 border-r bg-card p-4">
        <h3 className="font-semibold mb-4">Select Agent</h3>
        <div className="space-y-2">
          <a
            href="/chat/orchestrator"
            className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${
              agentId === 'orchestrator' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
            }`}
          >
            <Bot className="h-4 w-4" />
            <span className="text-sm">Orchestrator</span>
          </a>
          {agents.map((agent) => (
            <a
              key={agent.id}
              href={`/chat/${agent.id}`}
              className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${
                agentId === agent.id ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              }`}
            >
              <Bot className="h-4 w-4" />
              <span className="text-sm">{agent.name}</span>
            </a>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b p-4">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            <h2 className="font-semibold">{currentAgent.name}</h2>
            <span className={`ml-auto text-xs px-2 py-1 rounded-full ${
              isConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <div className="relative inline-block">
                <div className="absolute -inset-2 rounded-full blur-lg bg-primary/20" />
                <div className="relative h-12 w-12 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="h-6 w-6 text-primary" />
                </div>
              </div>
              <p className="mt-2">Start a conversation with {currentAgent.name}</p>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-3 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                </div>
              )}
              
              <div
                className={`max-w-[70%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                }`}
              >
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
                <div className="text-xs opacity-60 mt-1">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>

              {message.role === 'user' && (
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center">
                    <User className="h-4 w-4" />
                  </div>
                </div>
              )}
            </div>
          ))}

          {isTyping && (
            <div className="flex gap-3">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
              </div>
              <div className="bg-muted rounded-lg p-3">
                <span className="loading-dots inline-flex gap-1">
                  <span className="h-2 w-2 rounded-full bg-current"></span>
                  <span className="h-2 w-2 rounded-full bg-current"></span>
                  <span className="h-2 w-2 rounded-full bg-current"></span>
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              disabled={!isConnected}
              className="flex-1"
            />
            <Button
              onClick={sendMessage}
              disabled={!isConnected || !input.trim() || isTyping}
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}