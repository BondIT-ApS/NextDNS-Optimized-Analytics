import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Globe, Shield } from 'lucide-react'

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

interface TopDomainsData {
  blocked_domains: { domain: string; count: number; percentage: number }[]
  allowed_domains: { domain: string; count: number; percentage: number }[]
}

interface ChartJsDomainsProps {
  data: TopDomainsData | null
}

const LEGO_COLORS = {
  blue: '#0066CC',
  red: '#D91E18',
  green: '#00A83F',
  yellow: '#FFD700',
  orange: '#FF8C00',
  purple: '#7B68EE',
  gray: '#6B7280',
}

export function ChartJsDomains({ data }: ChartJsDomainsProps) {
  // Process data for charts
  const blockedData = data?.blocked_domains || []
  const allowedData = data?.allowed_domains || []

  // Truncate long domain names for display
  const truncateDomain = (domain: string, maxLength: number = 25) => {
    return domain.length > maxLength
      ? `${domain.substring(0, maxLength - 3)}...`
      : domain
  }

  // Common chart options for horizontal bar charts
  const horizontalBarOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y' as const,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
      tooltip: {
        callbacks: {
          title: function (context) {
            const index = context[0].dataIndex
            const isBlocked = context[0].dataset.label?.includes('Blocked')
            const originalDomain = isBlocked
              ? blockedData[index]?.domain
              : allowedData[index]?.domain
            return originalDomain || context[0].label
          },
          label: function (context) {
            const index = context.dataIndex
            const isBlocked = context.dataset.label?.includes('Blocked')
            const domainData = isBlocked
              ? blockedData[index]
              : allowedData[index]

            if (domainData) {
              return [
                `Count: ${domainData.count.toLocaleString()}`,
                `Percentage: ${domainData.percentage.toFixed(1)}%`,
              ]
            }
            return `${context.dataset.label}: ${context.parsed.x}`
          },
        },
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        grid: {
          color: 'rgba(107, 114, 128, 0.1)',
        },
        ticks: {
          font: {
            size: 10,
          },
        },
      },
      y: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 10,
          },
          maxRotation: 0,
          callback: function (value, index) {
            // Show truncated domain names
            const isBlocked =
              this.chart.data.datasets[0].label?.includes('Blocked')
            const domainData = isBlocked
              ? blockedData[index]
              : allowedData[index]
            return domainData ? truncateDomain(domainData.domain, 20) : value
          },
        },
      },
    },
  }

  // Blocked domains chart data
  const blockedChartData = {
    labels: blockedData.map(item => truncateDomain(item.domain, 20)),
    datasets: [
      {
        label: 'Blocked Domain Count',
        data: blockedData.map(item => item.count),
        backgroundColor: `${LEGO_COLORS.red}CC`,
        borderColor: LEGO_COLORS.red,
        borderWidth: 2,
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  }

  // Allowed domains chart data
  const allowedChartData = {
    labels: allowedData.map(item => truncateDomain(item.domain, 20)),
    datasets: [
      {
        label: 'Allowed Domain Count',
        data: allowedData.map(item => item.count),
        backgroundColor: `${LEGO_COLORS.green}CC`,
        borderColor: LEGO_COLORS.green,
        borderWidth: 2,
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Top Blocked Domains */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-red-600" />
            Top Blocked Domains
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            {blockedData.length > 0 ? (
              <Bar data={blockedChartData} options={horizontalBarOptions} />
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No blocked domains data available</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Top Allowed Domains */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5 text-green-600" />
            Top Allowed Domains
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            {allowedData.length > 0 ? (
              <Bar data={allowedChartData} options={horizontalBarOptions} />
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <Globe className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No allowed domains data available</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Domain Statistics Overview */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-600" />
            Domain Statistics Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {blockedData.length}
              </div>
              <div className="text-sm text-red-600 font-medium">
                Blocked Domains
              </div>
            </div>

            <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {allowedData.length}
              </div>
              <div className="text-sm text-green-600 font-medium">
                Allowed Domains
              </div>
            </div>

            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {blockedData
                  .reduce((sum, domain) => sum + domain.count, 0)
                  .toLocaleString()}
              </div>
              <div className="text-sm text-blue-600 font-medium">
                Total Blocked
              </div>
            </div>

            <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {allowedData
                  .reduce((sum, domain) => sum + domain.count, 0)
                  .toLocaleString()}
              </div>
              <div className="text-sm text-purple-600 font-medium">
                Total Allowed
              </div>
            </div>
          </div>

          {/* Top domains summary */}
          {(blockedData.length > 0 || allowedData.length > 0) && (
            <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
              {blockedData.length > 0 && (
                <div>
                  <h4 className="font-semibold text-red-600 mb-2">
                    Most Blocked:
                  </h4>
                  <div className="space-y-2">
                    {blockedData.slice(0, 3).map((domain, index) => (
                      <div
                        key={index}
                        className="flex justify-between items-center text-sm"
                      >
                        <span
                          className="font-mono text-xs truncate max-w-[200px]"
                          title={domain.domain}
                        >
                          {domain.domain}
                        </span>
                        <span className="font-semibold text-red-600">
                          {domain.count.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {allowedData.length > 0 && (
                <div>
                  <h4 className="font-semibold text-green-600 mb-2">
                    Most Requested:
                  </h4>
                  <div className="space-y-2">
                    {allowedData.slice(0, 3).map((domain, index) => (
                      <div
                        key={index}
                        className="flex justify-between items-center text-sm"
                      >
                        <span
                          className="font-mono text-xs truncate max-w-[200px]"
                          title={domain.domain}
                        >
                          {domain.domain}
                        </span>
                        <span className="font-semibold text-green-600">
                          {domain.count.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
