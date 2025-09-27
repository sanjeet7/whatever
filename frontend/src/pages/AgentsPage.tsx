import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bot, Plus, Code, Search, FileText, Database } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { agentsAPI, toolsAPI } from '@/lib/api'
import type { Agent, Tool } from '@/types'
import toast from 'react-hot-toast'

const toolIcons: Record<string, any> = {
  web_search: Search,
  code_analysis: Code,
  content_generation: FileText,
  data_access: Database,
}

export function AgentsPage() {
  const queryClient = useQueryClient()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    instructions: '',
    model: 'gpt-4-turbo-preview',
    tools: [] as string[],
  })

  const { data: agents = [], isLoading } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: agentsAPI.list,
  })

  const { data: availableTools = [] } = useQuery<Tool[]>({
    queryKey: ['tools'],
    queryFn: toolsAPI.list,
  })

  const createMutation = useMutation({
    mutationFn: agentsAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
      toast.success('Agent created successfully!')
      setShowCreateForm(false)
      setFormData({
        name: '',
        instructions: '',
        model: 'gpt-4-turbo-preview',
        tools: [],
      })
    },
    onError: () => {
      toast.error('Failed to create agent')
    },
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData)
  }

  const toggleTool = (toolName: string) => {
    setFormData(prev => ({
      ...prev,
      tools: prev.tools.includes(toolName)
        ? prev.tools.filter(t => t !== toolName)
        : [...prev.tools, toolName]
    }))
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Agents</h1>
          <p className="text-muted-foreground mt-2">
            Manage your AI agents and create new ones
          </p>
        </div>
        <Button onClick={() => setShowCreateForm(!showCreateForm)}>
          <Plus className="mr-2 h-4 w-4" />
          New Agent
        </Button>
      </div>

      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Agent</CardTitle>
            <CardDescription>
              Define your agent's behavior and capabilities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Agent Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., Customer Support Agent"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="instructions">Instructions</Label>
                <Textarea
                  id="instructions"
                  placeholder="Describe what this agent should do and how it should behave..."
                  value={formData.instructions}
                  onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                  rows={4}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label>Tools</Label>
                <div className="grid grid-cols-2 gap-2">
                  {availableTools.map((tool) => {
                    const Icon = toolIcons[tool.name] || Bot
                    const isSelected = formData.tools.includes(tool.name)
                    return (
                      <button
                        key={tool.name}
                        type="button"
                        onClick={() => toggleTool(tool.name)}
                        className={`flex items-center gap-2 p-3 rounded-lg border text-sm transition-colors ${
                          isSelected
                            ? 'border-primary bg-primary/10 text-primary'
                            : 'border-input hover:bg-accent'
                        }`}
                      >
                        <Icon className="h-4 w-4" />
                        <span className="font-medium">{tool.description}</span>
                      </button>
                    )
                  })}
                </div>
              </div>

              <div className="flex gap-4 pt-4">
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Agent'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowCreateForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <Card key={agent.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className="h-5 w-5 text-primary" />
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                  </div>
                </div>
                <CardDescription className="text-xs">
                  Model: {agent.model}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm font-medium mb-1">Tools</p>
                    <div className="flex flex-wrap gap-1">
                      {agent.tools.length > 0 ? (
                        agent.tools.map((tool) => {
                          const Icon = toolIcons[tool] || Bot
                          return (
                            <div
                              key={tool}
                              className="flex items-center gap-1 px-2 py-1 bg-secondary rounded-md text-xs"
                            >
                              <Icon className="h-3 w-3" />
                              <span>{tool}</span>
                            </div>
                          )
                        })
                      ) : (
                        <span className="text-xs text-muted-foreground">No tools</span>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => window.location.href = `/chat/${agent.id}`}
                  >
                    Start Chat
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}