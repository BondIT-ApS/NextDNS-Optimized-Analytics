import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Database } from 'lucide-react'

export function Logs() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">DNS Logs</h1>
        <p className="text-muted-foreground">View and analyze DNS queries</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5 text-lego-blue" />
            Coming Soon
          </CardTitle>
          <CardDescription>
            Advanced DNS logs table with filtering, pagination, and real-time updates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            🧱 This feature is being built, brick by brick! The advanced DNS logs table 
            will include filtering, search, pagination, and real-time updates.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}