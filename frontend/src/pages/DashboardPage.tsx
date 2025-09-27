import { useQuery } from '@tanstack/react-query'
import { Bot, MessageSquare, Sparkles, Activity } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { analyticsAPI } from '@/lib/api'
import type { AnalyticsData } from '@/types'

export function DashboardPage() {
  const { data: analytics, isLoading } = useQuery<AnalyticsData>({
    queryKey: ['analytics'],
    queryFn: analyticsAPI.getUsage,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const stats = [
    {
      title: 'Total Agents',
      value: analytics?.total_agents ?? 0,
      icon: Bot,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Active Sessions',
      value: analytics?.total_sessions ?? 0,
      icon: MessageSquare,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Active Connections',
      value: analytics?.active_connections ?? 0,
      icon: Activity,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Your Sessions',
      value: analytics?.user_sessions ?? 0,
      icon: Sparkles,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Monitor your AI agents and platform usage
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {isLoading ? '...' : stat.value}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <a
              href="/meta-agent"
              className="flex items-center gap-3 p-3 rounded-lg border hover:bg-accent transition-colors"
            >
              <Sparkles className="h-5 w-5 text-primary" />
              <div>
                <p className="font-medium">Design a New Agent</p>
                <p className="text-sm text-muted-foreground">
                  Use the Meta Agent to create custom AI agents
                </p>
              </div>
            </a>
            <a
              href="/chat"
              className="flex items-center gap-3 p-3 rounded-lg border hover:bg-accent transition-colors"
            >
              <MessageSquare className="h-5 w-5 text-primary" />
              <div>
                <p className="font-medium">Start a Conversation</p>
                <p className="text-sm text-muted-foreground">
                  Chat with your AI agents in real-time
                </p>
              </div>
            </a>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Platform Features</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="mt-1 h-2 w-2 rounded-full bg-green-500" />
              <div>
                <p className="font-medium">OpenAI Agents SDK</p>
                <p className="text-sm text-muted-foreground">
                  Powered by the official OpenAI Agents SDK
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="mt-1 h-2 w-2 rounded-full bg-green-500" />
              <div>
                <p className="font-medium">Agent Handoffs</p>
                <p className="text-sm text-muted-foreground">
                  Seamless transitions between specialized agents
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="mt-1 h-2 w-2 rounded-full bg-green-500" />
              <div>
                <p className="font-medium">Real-time Chat</p>
                <p className="text-sm text-muted-foreground">
                  WebSocket-powered instant messaging
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="mt-1 h-2 w-2 rounded-full bg-green-500" />
              <div>
                <p className="font-medium">Meta Agent Designer</p>
                <p className="text-sm text-muted-foreground">
                  AI-powered agent creation assistant
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}