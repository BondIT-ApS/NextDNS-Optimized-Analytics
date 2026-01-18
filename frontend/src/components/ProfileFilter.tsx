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
  Layers,
  Search,
  ChevronDown,
  ChevronUp,
  X,
  CheckSquare,
  Square,
} from 'lucide-react'

interface ProfileFilterProps {
  availableProfiles: string[]
  selectedProfiles: string[]
  onProfileSelectionChange: (profiles: string[]) => void
  profileColors: Record<string, string>
  profileNames?: Record<string, string> // Optional profile ID to name mapping
}

export const ProfileFilter = memo<ProfileFilterProps>(
  ({
    availableProfiles,
    selectedProfiles,
    onProfileSelectionChange,
    profileColors,
    profileNames = {},
  }) => {
    const [isExpanded, setIsExpanded] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')

    // Filter profiles based on search query
    const filteredProfiles = useMemo(() => {
      if (!searchQuery.trim()) return availableProfiles
      return availableProfiles.filter(profileId => {
        const name = profileNames[profileId] || profileId
        return name.toLowerCase().includes(searchQuery.toLowerCase())
      })
    }, [availableProfiles, searchQuery, profileNames])

    const handleProfileToggle = (profileId: string) => {
      const isSelected = selectedProfiles.includes(profileId)
      if (isSelected) {
        onProfileSelectionChange(selectedProfiles.filter(p => p !== profileId))
      } else {
        onProfileSelectionChange([...selectedProfiles, profileId])
      }
    }

    const handleSelectAll = () => {
      onProfileSelectionChange(filteredProfiles)
    }

    const handleSelectNone = () => {
      onProfileSelectionChange([])
    }

    const handleRemoveProfile = (profileId: string) => {
      onProfileSelectionChange(selectedProfiles.filter(p => p !== profileId))
    }

    const getProfileDisplayName = (profileId: string): string => {
      return profileNames[profileId] || profileId
    }

    // Don't show the filter if no profiles available
    if (!availableProfiles || availableProfiles.length === 0) {
      return (
        <Card className="opacity-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Layers className="h-5 w-5" />
              Profile Filter
            </CardTitle>
            <CardDescription>
              No profiles available. Start fetching data.
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
                <Layers className="h-5 w-5" />
                Profile Filter
                {selectedProfiles.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {selectedProfiles.length}
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                Select profiles to display in the chart
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

        {/* Selected profiles display (always visible) */}
        {selectedProfiles.length > 0 && (
          <CardContent className="pt-0">
            <div className="flex flex-wrap gap-2">
              {selectedProfiles.map(profileId => (
                <Badge
                  key={profileId}
                  variant="default"
                  className="flex items-center gap-2"
                  style={{
                    backgroundColor: `${profileColors[profileId]}20`,
                    borderColor: profileColors[profileId],
                    borderWidth: '2px',
                    color: 'inherit',
                  }}
                >
                  <div
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: profileColors[profileId] }}
                  />
                  {getProfileDisplayName(profileId)}
                  <button
                    onClick={() => handleRemoveProfile(profileId)}
                    className="ml-1 hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </CardContent>
        )}

        {/* Expanded profile selection */}
        {isExpanded && (
          <CardContent className={selectedProfiles.length > 0 ? 'pt-0' : ''}>
            <div className="space-y-4">
              {/* Search input */}
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search profiles..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
              </div>

              {/* Select all/none buttons */}
              {filteredProfiles.length > 0 && (
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSelectAll}
                    disabled={filteredProfiles.every(profile =>
                      selectedProfiles.includes(profile)
                    )}
                  >
                    Select All
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSelectNone}
                    disabled={selectedProfiles.length === 0}
                  >
                    Clear All
                  </Button>
                </div>
              )}

              {/* Profile list */}
              <div className="max-h-60 overflow-y-auto space-y-1">
                {filteredProfiles.length === 0 ? (
                  <div className="text-sm text-muted-foreground text-center py-4">
                    {searchQuery
                      ? 'No profiles match your search.'
                      : 'No profiles found.'}
                  </div>
                ) : (
                  filteredProfiles.map(profileId => {
                    const isSelected = selectedProfiles.includes(profileId)
                    return (
                      <div
                        key={profileId}
                        className="flex items-center space-x-2 p-2 hover:bg-muted rounded cursor-pointer"
                        onClick={() => handleProfileToggle(profileId)}
                      >
                        <div
                          className="h-3 w-3 rounded-full"
                          style={{ backgroundColor: profileColors[profileId] }}
                        />
                        {isSelected ? (
                          <CheckSquare className="h-4 w-4 text-primary" />
                        ) : (
                          <Square className="h-4 w-4 text-muted-foreground" />
                        )}
                        <span className="text-sm font-medium">
                          {getProfileDisplayName(profileId)}
                        </span>
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          </CardContent>
        )}
      </Card>
    )
  }
)

ProfileFilter.displayName = 'ProfileFilter'
