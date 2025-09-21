import { memo, useState, useMemo } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Smartphone,
  Search,
  ChevronDown,
  ChevronUp,
  X,
  CheckSquare,
  Square,
} from 'lucide-react'
import { useDeviceNames } from '@/hooks/useDevices'

interface DeviceFilterProps {
  selectedProfile?: string
  selectedDevices: string[]
  onDeviceSelectionChange: (devices: string[]) => void
  timeRange?: string
}

export const DeviceFilter = memo<DeviceFilterProps>(
  ({
    selectedProfile,
    selectedDevices,
    onDeviceSelectionChange,
    timeRange = '24h',
  }) => {
    const [isExpanded, setIsExpanded] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')

    const { deviceNames, isLoading, error } = useDeviceNames(
      selectedProfile,
      timeRange
    )

    // Filter devices based on search query
    const filteredDevices = useMemo(() => {
      if (!searchQuery.trim()) return deviceNames
      return deviceNames.filter((device: string) =>
        device.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }, [deviceNames, searchQuery])

    const handleDeviceToggle = (deviceName: string) => {
      const isSelected = selectedDevices.includes(deviceName)
      if (isSelected) {
        onDeviceSelectionChange(selectedDevices.filter(d => d !== deviceName))
      } else {
        onDeviceSelectionChange([...selectedDevices, deviceName])
      }
    }

    const handleSelectAll = () => {
      onDeviceSelectionChange(filteredDevices)
    }

    const handleSelectNone = () => {
      onDeviceSelectionChange([])
    }

    const handleRemoveDevice = (deviceName: string) => {
      onDeviceSelectionChange(selectedDevices.filter(d => d !== deviceName))
    }

    // Don't show the filter if no profile is selected
    if (!selectedProfile) {
      return (
        <Card className="opacity-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Smartphone className="h-5 w-5" />
              Device Filter
            </CardTitle>
            <CardDescription>
              Select a profile to see available devices
            </CardDescription>
          </CardHeader>
        </Card>
      )
    }

    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Smartphone className="h-5 w-5" />
                Device Filter
                {selectedDevices.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {selectedDevices.length}
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                Filter by specific devices
                {selectedProfile && ` for profile ${selectedProfile}`}
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-4 w-4" />
                  Collapse
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4" />
                  Expand
                </>
              )}
            </Button>
          </div>
        </CardHeader>

        {/* Selected devices display (always visible) */}
        {selectedDevices.length > 0 && (
          <CardContent className="pt-0">
            <div className="flex flex-wrap gap-2">
              {selectedDevices.map(device => (
                <Badge
                  key={device}
                  variant="default"
                  className="flex items-center gap-1"
                >
                  {device}
                  <button
                    onClick={() => handleRemoveDevice(device)}
                    className="ml-1 hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </CardContent>
        )}

        {/* Expanded device selection */}
        {isExpanded && (
          <CardContent className={selectedDevices.length > 0 ? 'pt-0' : ''}>
            {isLoading ? (
              <div className="space-y-2">
                <div className="h-8 bg-muted animate-pulse rounded"></div>
                <div className="h-32 bg-muted animate-pulse rounded"></div>
              </div>
            ) : error ? (
              <div className="text-sm text-destructive">
                Failed to load devices. Try selecting a different profile.
              </div>
            ) : (
              <div className="space-y-4">
                {/* Search input */}
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search devices..."
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    className="pl-8"
                  />
                </div>

                {/* Select all/none buttons */}
                {filteredDevices.length > 0 && (
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleSelectAll}
                      disabled={filteredDevices.every(device =>
                        selectedDevices.includes(device)
                      )}
                    >
                      Select All
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleSelectNone}
                      disabled={selectedDevices.length === 0}
                    >
                      Clear All
                    </Button>
                  </div>
                )}

                {/* Device list */}
                <div className="max-h-60 overflow-y-auto space-y-1">
                  {filteredDevices.length === 0 ? (
                    <div className="text-sm text-muted-foreground text-center py-4">
                      {searchQuery
                        ? 'No devices match your search.'
                        : 'No devices found for this profile.'}
                    </div>
                  ) : (
                    filteredDevices.map(device => {
                      const isSelected = selectedDevices.includes(device)
                      return (
                        <div
                          key={device}
                          className="flex items-center space-x-2 p-2 hover:bg-muted rounded cursor-pointer"
                          onClick={() => handleDeviceToggle(device)}
                        >
                          {isSelected ? (
                            <CheckSquare className="h-4 w-4 text-primary" />
                          ) : (
                            <Square className="h-4 w-4 text-muted-foreground" />
                          )}
                          <span className="text-sm font-medium">{device}</span>
                        </div>
                      )
                    })
                  )}
                </div>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    )
  }
)

DeviceFilter.displayName = 'DeviceFilter'
