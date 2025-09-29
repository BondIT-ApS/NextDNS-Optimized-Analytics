import { memo, useCallback } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Clock, Database, CheckCircle, XCircle } from 'lucide-react'
import type { DNSLog } from '@/types/api'

interface LogsTableProps {
  logs: DNSLog[]
  debouncedSearchQuery: string
  statusFilter: 'all' | 'blocked' | 'allowed'
}

export const LogsTable = memo<LogsTableProps>(
  ({ logs, debouncedSearchQuery, statusFilter }) => {
    const formatTime = useCallback((timestamp: string) => {
      return new Date(timestamp).toLocaleTimeString()
    }, [])

    const formatDevice = useCallback((device: DNSLog['device']) => {
      if (!device) return 'Unknown'
      if (typeof device === 'string') return device
      return (device as { name?: string; id?: string }).name ||
        (device as { name?: string; id?: string }).id ||
        'Unknown'
    }, [])

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            DNS Query Log
          </CardTitle>
          <CardDescription>
            {logs.length > 0
              ? `${logs.length} recent DNS queries`
              : 'No logs match your filters'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <div className="text-center py-8">
              <Database className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">
                No logs found
              </h3>
              <p className="text-muted-foreground">
                {debouncedSearchQuery || statusFilter !== 'all'
                  ? 'Try adjusting your filters'
                  : 'No DNS logs available'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                      Time
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                      Domain
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                      Device
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                      Status
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                      Type
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log, index: number) => (
                    <tr
                      key={`${log.id}-${index}`}
                      className="border-b hover:bg-muted/50 transition-colors"
                    >
                      <td className="py-3 px-4 font-mono text-sm">
                        {formatTime(log.timestamp)}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-medium">{log.domain}</div>
                      </td>
                      <td className="py-3 px-4 text-sm text-muted-foreground">
                        {formatDevice(log.device)}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          {log.blocked ? (
                            <>
                              <XCircle className="h-4 w-4 text-lego-red" />
                              <span className="text-lego-red font-medium">
                                Blocked
                              </span>
                            </>
                          ) : (
                            <>
                              <CheckCircle className="h-4 w-4 text-lego-green" />
                              <span className="text-lego-green font-medium">
                                Allowed
                              </span>
                            </>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4 font-mono text-sm">
                        {log.query_type}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }
)

LogsTable.displayName = 'LogsTable'
