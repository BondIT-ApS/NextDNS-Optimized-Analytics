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

interface TopTLDsData {
  blocked_tlds: { domain: string; count: number; percentage: number }[]
  allowed_tlds: { domain: string; count: number; percentage: number }[]
}

interface ChartJsTldsProps {
  data: TopTLDsData | null
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

export function ChartJsTlds({ data }: ChartJsTldsProps) {
  // Process data for charts
  const blockedTlds = data?.blocked_tlds || []
  const allowedTlds = data?.allowed_tlds || []

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
          label: function (context) {
            const index = context.dataIndex
            const isBlocked = context.dataset.label?.includes('Blocked')
            const tldData = isBlocked ? blockedTlds[index] : allowedTlds[index]

            if (tldData) {
              return [
                `Count: ${tldData.count.toLocaleString()}`,
                `Percentage: ${tldData.percentage.toFixed(1)}%`,
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
        },
      },
    },
  }

  // Blocked TLDs chart data
  const blockedChartData = {
    labels: blockedTlds.map(item => item.domain),
    datasets: [
      {
        label: 'Blocked TLD Count',
        data: blockedTlds.map(item => item.count),
        backgroundColor: `${LEGO_COLORS.red}CC`,
        borderColor: LEGO_COLORS.red,
        borderWidth: 2,
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  }

  // Allowed TLDs chart data
  const allowedChartData = {
    labels: allowedTlds.map(item => item.domain),
    datasets: [
      {
        label: 'Allowed TLD Count',
        data: allowedTlds.map(item => item.count),
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
      {/* Top Blocked TLDs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-red-600" />
            Top Blocked Parent Domains
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            {blockedTlds.length > 0 ? (
              <Bar data={blockedChartData} options={horizontalBarOptions} />
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No blocked parent domains data available</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Top Allowed TLDs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5 text-green-600" />
            Top Allowed Parent Domains
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            {allowedTlds.length > 0 ? (
              <Bar data={allowedChartData} options={horizontalBarOptions} />
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <Globe className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No allowed parent domains data available</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* TLD Statistics Overview */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-600" />
            Parent Domain Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {blockedTlds.length}
              </div>
              <div className="text-sm text-red-600 font-medium">
                Blocked Parent Domains
              </div>
            </div>

            <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {allowedTlds.length}
              </div>
              <div className="text-sm text-green-600 font-medium">
                Allowed Parent Domains
              </div>
            </div>

            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {blockedTlds
                  .reduce((sum, tld) => sum + tld.count, 0)
                  .toLocaleString()}
              </div>
              <div className="text-sm text-blue-600 font-medium">
                Total Blocked Requests
              </div>
            </div>

            <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {allowedTlds
                  .reduce((sum, tld) => sum + tld.count, 0)
                  .toLocaleString()}
              </div>
              <div className="text-sm text-purple-600 font-medium">
                Total Allowed Requests
              </div>
            </div>
          </div>

          {/* Top TLDs summary */}
          {(blockedTlds.length > 0 || allowedTlds.length > 0) && (
            <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
              {blockedTlds.length > 0 && (
                <div>
                  <h4 className="font-semibold text-red-600 mb-2">
                    Most Blocked Parent Domains:
                  </h4>
                  <div className="space-y-2">
                    {blockedTlds.slice(0, 3).map((tld, index) => (
                      <div
                        key={index}
                        className="flex justify-between items-center text-sm"
                      >
                        <span
                          className="font-mono text-xs truncate max-w-[200px]"
                          title={tld.domain}
                        >
                          {tld.domain}
                        </span>
                        <span className="font-semibold text-red-600">
                          {tld.count.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {allowedTlds.length > 0 && (
                <div>
                  <h4 className="font-semibold text-green-600 mb-2">
                    Most Requested Parent Domains:
                  </h4>
                  <div className="space-y-2">
                    {allowedTlds.slice(0, 3).map((tld, index) => (
                      <div
                        key={index}
                        className="flex justify-between items-center text-sm"
                      >
                        <span
                          className="font-mono text-xs truncate max-w-[200px]"
                          title={tld.domain}
                        >
                          {tld.domain}
                        </span>
                        <span className="font-semibold text-green-600">
                          {tld.count.toLocaleString()}
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