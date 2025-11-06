import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions,
} from 'chart.js'
import { Line, Pie, Bar } from 'react-chartjs-2'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { format } from 'date-fns'
import {
  Activity,
  TrendingUp,
  PieChart as PieChartIcon,
  BarChart,
} from 'lucide-react'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface TimeSeriesDataPoint {
  timestamp: string
  total_queries: number
  blocked_queries: number
  allowed_queries: number
}

interface TimeSeriesData {
  data: TimeSeriesDataPoint[]
  granularity: string
  total_points: number
}

interface StatsOverview {
  total_queries: number
  blocked_queries: number
  allowed_queries: number
  blocked_percentage: number
  queries_per_hour: number
  most_active_device: string | null
  top_blocked_domain: string | null
}

interface ChartJsOverviewProps {
  data: TimeSeriesData | null
  overview: StatsOverview
}

// LEGO-themed colors
const LEGO_COLORS = {
  blue: '#0066CC',
  red: '#D91E18',
  green: '#00A83F',
  yellow: '#FFD700',
  orange: '#FF8C00',
  purple: '#7B68EE',
  gray: '#6B7280',
}

export function ChartJsOverview({ data, overview }: ChartJsOverviewProps) {
  // Handle null data case
  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="col-span-2">
          <CardContent className="pt-6">
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No time series data available</p>
                <p className="text-sm mt-2">
                  Data will appear here once DNS queries are collected
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Process time series data for charts
  const timeSeriesData = data.data

  // Format labels based on granularity
  const formatTimestamp = (timestamp: string, granularity: string) => {
    const date = new Date(timestamp)

    switch (granularity) {
      case '5min':
        // For 1-hour range, show time like 14:00, 14:05, 14:10
        return format(date, 'HH:mm')
      case 'minute':
        return format(date, 'HH:mm')
      case 'hour':
        // For 24-hour range, show hourly like 12:00, 13:00, 14:00
        return format(date, 'HH:mm')
      case 'day':
        // For 7d/30d ranges, show dates like Jan 15, Jan 16
        return format(date, 'MMM dd')
      default:
        return format(date, 'HH:mm')
    }
  }

  const labels = timeSeriesData.map(point =>
    formatTimestamp(point.timestamp, data?.granularity || 'hour')
  )

  // Common chart options
  const commonOptions: ChartOptions<any> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: {
            size: 12,
          },
        },
      },
      title: {
        display: false,
      },
    },
    scales: {
      x: {
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
          color: 'rgba(107, 114, 128, 0.1)',
        },
        ticks: {
          font: {
            size: 10,
          },
        },
      },
    },
  }

  // Line chart data
  const lineChartData = {
    labels,
    datasets: [
      {
        label: 'Total Queries',
        data: timeSeriesData.map(point => point.total_queries),
        borderColor: LEGO_COLORS.blue,
        backgroundColor: `${LEGO_COLORS.blue}20`,
        borderWidth: 3,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: LEGO_COLORS.blue,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        tension: 0.4,
      },
      {
        label: 'Blocked',
        data: timeSeriesData.map(point => point.blocked_queries),
        borderColor: LEGO_COLORS.red,
        backgroundColor: `${LEGO_COLORS.red}20`,
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: LEGO_COLORS.red,
        tension: 0.4,
      },
      {
        label: 'Allowed',
        data: timeSeriesData.map(point => point.allowed_queries),
        borderColor: LEGO_COLORS.green,
        backgroundColor: `${LEGO_COLORS.green}20`,
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: LEGO_COLORS.green,
        tension: 0.4,
      },
    ],
  }

  // Pie chart data
  const pieChartData = {
    labels: ['Blocked', 'Allowed'],
    datasets: [
      {
        data: [overview.blocked_queries, overview.allowed_queries],
        backgroundColor: [LEGO_COLORS.red, LEGO_COLORS.green],
        borderColor: ['#ffffff', '#ffffff'],
        borderWidth: 3,
        hoverOffset: 10,
      },
    ],
  }

  // Bar chart data for hourly breakdown
  const barChartData = {
    labels,
    datasets: [
      {
        label: 'Blocked',
        data: timeSeriesData.map(point => point.blocked_queries),
        backgroundColor: `${LEGO_COLORS.red}80`,
        borderColor: LEGO_COLORS.red,
        borderWidth: 2,
        borderRadius: 4,
        borderSkipped: false,
      },
      {
        label: 'Allowed',
        data: timeSeriesData.map(point => point.allowed_queries),
        backgroundColor: `${LEGO_COLORS.green}80`,
        borderColor: LEGO_COLORS.green,
        borderWidth: 2,
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  }

  // Area chart data with cumulative values (using Line with fill)
  const calculateCumulativeData = (data: number[]) => {
    let cumulative = 0
    return data.map(value => {
      cumulative += value
      return cumulative
    })
  }

  const areaChartData = {
    labels,
    datasets: [
      {
        label: 'Cumulative Total Queries',
        data: calculateCumulativeData(
          timeSeriesData.map(point => point.total_queries)
        ),
        borderColor: LEGO_COLORS.blue,
        backgroundColor: `${LEGO_COLORS.blue}40`,
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 6,
        pointBackgroundColor: LEGO_COLORS.blue,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
      },
      {
        label: 'Cumulative Blocked',
        data: calculateCumulativeData(
          timeSeriesData.map(point => point.blocked_queries)
        ),
        borderColor: LEGO_COLORS.red,
        backgroundColor: `${LEGO_COLORS.red}30`,
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 1,
        pointHoverRadius: 4,
        pointBackgroundColor: LEGO_COLORS.red,
      },
      {
        label: 'Cumulative Allowed',
        data: calculateCumulativeData(
          timeSeriesData.map(point => point.allowed_queries)
        ),
        borderColor: LEGO_COLORS.green,
        backgroundColor: `${LEGO_COLORS.green}30`,
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 1,
        pointHoverRadius: 4,
        pointBackgroundColor: LEGO_COLORS.green,
      },
    ],
  }

  const areaOptions: ChartOptions<'line'> = {
    ...commonOptions,
    elements: {
      point: {
        radius: 1,
      },
    },
    plugins: {
      ...commonOptions.plugins,
      filler: {
        propagate: false,
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            const label = context.dataset.label || ''
            const value = context.parsed.y
            return `${label}: ${(value ?? 0).toLocaleString()}`
          },
          afterBody: function (tooltipItems) {
            // Show the increment for this time period
            const dataIndex = tooltipItems[0].dataIndex
            if (dataIndex > 0) {
              const current = tooltipItems[0].parsed.y ?? 0
              const previous = tooltipItems[0].dataset.data[
                dataIndex - 1
              ] as number
              const increment = current - previous
              return [``, `Increment: +${increment.toLocaleString()}`]
            }
            return []
          },
        },
      },
    },
  }

  const pieOptions: ChartOptions<'pie'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          font: {
            size: 12,
          },
          padding: 20,
        },
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            const total = overview.total_queries
            const value = context.parsed
            const percentage = ((value / total) * 100).toFixed(1)
            return `${context.label}: ${value.toLocaleString()} (${percentage}%)`
          },
        },
      },
    },
  }

  const barOptions: ChartOptions<'bar'> = {
    ...commonOptions,
    scales: {
      ...commonOptions.scales,
      x: {
        ...commonOptions.scales?.x,
        stacked: true,
      },
      y: {
        ...commonOptions.scales?.y,
        stacked: true,
      },
    },
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Queries Over Time - Line Chart */}
      <Card className="col-span-1 lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            Queries Over Time
            <span className="text-sm font-normal text-muted-foreground ml-2">
              {data?.granularity} intervals
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <Line data={lineChartData} options={commonOptions} />
          </div>
        </CardContent>
      </Card>

      {/* Cumulative Query Volume - Area Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-purple-600" />
            Cumulative Query Volume
            <span className="text-sm font-normal text-muted-foreground ml-2">
              accumulated over time
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <Line data={areaChartData} options={areaOptions} />
          </div>
        </CardContent>
      </Card>

      {/* Blocked vs Allowed - Pie Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PieChartIcon className="h-5 w-5 text-orange-600" />
            Blocked vs Allowed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <Pie data={pieChartData} options={pieOptions} />
          </div>
        </CardContent>
      </Card>

      {/* Query Breakdown - Stacked Bar Chart */}
      <Card className="col-span-1 lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart className="h-5 w-5 text-green-600" />
            Query Breakdown by Time
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <Bar data={barChartData} options={barOptions} />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
