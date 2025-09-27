import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, Wand2, Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { metaAgentAPI, agentsAPI } from '@/lib/api'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'

export function MetaAgentPage() {
  const [requirements, setRequirements] = useState('')
  const [design, setDesign] = useState<any>(null)
  const [copied, setCopied] = useState(false)

  const designMutation = useMutation({
    mutationFn: metaAgentAPI.design,
    onSuccess: (data) => {
      setDesign(data)
      toast.success('Agent design generated successfully!')
    },
    onError: () => {
      toast.error('Failed to generate agent design')
    },
  })

  const createMutation = useMutation({
    mutationFn: agentsAPI.create,
    onSuccess: () => {
      toast.success('Agent created successfully!')
      setDesign(null)
      setRequirements('')
    },
    onError: () => {
      toast.error('Failed to create agent')
    },
  })

  const handleDesign = () => {
    if (!requirements.trim()) {
      toast.error('Please describe what you want the agent to do')
      return
    }
    designMutation.mutate(requirements)
  }

  const handleCreate = () => {
    if (!design?.suggested_config) return
    createMutation.mutate(design.suggested_config)
  }

  const copyConfig = () => {
    if (!design?.suggested_config) return
    navigator.clipboard.writeText(JSON.stringify(design.suggested_config, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    toast.success('Configuration copied to clipboard')
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Sparkles className="h-8 w-8 text-primary glow rounded-full" />
          Meta Agent Designer
        </h1>
        <p className="text-muted-foreground mt-2">
          Describe what you want your AI agent to do, and let our Meta Agent design it for you
        </p>
      </div>

      <Card className="neo-panel">
        <CardHeader>
          <CardTitle>Agent Requirements</CardTitle>
          <CardDescription>
            Be specific about the agent's purpose, capabilities, and behavior
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="requirements">What should your agent do?</Label>
            <Textarea
              id="requirements"
              placeholder="Example: I need an agent that can help users with technical support. It should be able to answer questions about our software, troubleshoot common issues, and escalate complex problems. The agent should be friendly, patient, and technically knowledgeable."
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              rows={6}
              className="resize-none"
            />
          </div>
          
          <Button 
            onClick={handleDesign} 
            disabled={designMutation.isPending || !requirements.trim()}
            className="w-full"
          >
            {designMutation.isPending ? (
              <>
                Designing Agent
                <span className="ml-2 loading-dots inline-flex gap-1 align-middle">
                  <span className="h-2 w-2 rounded-full bg-current"></span>
                  <span className="h-2 w-2 rounded-full bg-current"></span>
                  <span className="h-2 w-2 rounded-full bg-current"></span>
                </span>
              </>
            ) : (
              <>
                <Wand2 className="mr-2 h-4 w-4" />
                Design Agent
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {design && (
        <Card className="neo-panel">
          <CardHeader>
            <CardTitle>Agent Design</CardTitle>
            <CardDescription>
              Review the generated agent configuration
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{design.design}</ReactMarkdown>
            </div>

            {design.suggested_config && (
              <>
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold">Configuration</h4>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={copyConfig}
                    >
                      {copied ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
                    <code>{JSON.stringify(design.suggested_config, null, 2)}</code>
                  </pre>
                </div>

                <div className="flex gap-4">
                  <Button
                    onClick={handleCreate}
                    disabled={createMutation.isPending}
                    className="flex-1"
                  >
                    {createMutation.isPending ? 'Creating...' : 'Create Agent'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setDesign(null)
                      setRequirements('')
                    }}
                    className="flex-1"
                  >
                    Start Over
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Tips for Better Agent Design</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>Be specific about the agent's primary purpose and goals</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>Describe the tone and personality you want the agent to have</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>List specific capabilities or tools the agent should have access to</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>Include any constraints or limitations the agent should follow</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>Provide examples of typical interactions or use cases</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}