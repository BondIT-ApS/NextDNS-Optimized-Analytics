import { memo, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2, Users, AlertCircle } from 'lucide-react'
import { useProfiles, useProfilesInfo } from '@/hooks/useLogs'

interface ProfileSelectorProps {
  selectedProfile?: string
  onProfileChange: (profileId: string | undefined) => void
  showStats?: boolean
}

export const ProfileSelector = memo<ProfileSelectorProps>(({ 
  selectedProfile, 
  onProfileChange, 
  showStats = true 
}) => {
  const { 
    data: profilesData, 
    isLoading: profilesLoading, 
    error: profilesError 
  } = useProfiles()
  
  const { 
    data: profilesInfo, 
    isLoading: infoLoading 
  } = useProfilesInfo()

  const profileOptions = useMemo(() => {
    if (!profilesData?.profiles) return []
    
    return profilesData.profiles.map(profile => {
      const info = profilesInfo?.profiles[profile.profile_id]
      const displayName = info?.name 
        ? `${info.name} (${profile.profile_id})`
        : `Profile ${profile.profile_id}`
        
      return {
        id: profile.profile_id,
        name: displayName,
        recordCount: profile.record_count,
        lastActivity: profile.last_activity,
        hasError: info?.error,
        isConfigured: !!info
      }
    }).sort((a, b) => b.recordCount - a.recordCount) // Sort by record count descending
  }, [profilesData, profilesInfo])

  if (profilesLoading || infoLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Users className="h-5 w-5" />
            Profile Filter
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading profiles...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (profilesError || !profilesData) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg text-destructive">
            <AlertCircle className="h-5 w-5" />
            Profile Filter
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Failed to load profiles. Please check your configuration.
          </p>
        </CardContent>
      </Card>
    )
  }

  if (profileOptions.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Users className="h-5 w-5" />
            Profile Filter
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No profiles found. Start collecting data to see available profiles.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Users className="h-5 w-5" />
          Profile Filter
        </CardTitle>
        {profileOptions.length > 0 && (
          <p className="text-sm text-muted-foreground">
            Filter logs by NextDNS profile ({profileOptions.length} available)
          </p>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {/* All Profiles Button */}
          <Button
            variant={!selectedProfile ? "default" : "outline"}
            size="sm"
            onClick={() => onProfileChange(undefined)}
            className="w-full justify-start"
          >
            <span className="font-medium">All Profiles</span>
            {showStats && profilesData && (
              <Badge variant="secondary" className="ml-auto">
                {profilesData.profiles.reduce((sum, p) => sum + p.record_count, 0).toLocaleString()} logs
              </Badge>
            )}
          </Button>

          {/* Individual Profile Buttons */}
          {profileOptions.map((profile) => (
            <Button
              key={profile.id}
              variant={selectedProfile === profile.id ? "default" : "outline"}
              size="sm"
              onClick={() => onProfileChange(profile.id)}
              className="w-full justify-start text-left"
            >
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">
                  {profile.name}
                </div>
                {profile.hasError && (
                  <div className="text-xs text-destructive">
                    <AlertCircle className="inline h-3 w-3 mr-1" />
                    Profile info unavailable
                  </div>
                )}
              </div>
              {showStats && (
                <div className="flex items-center gap-2 ml-2">
                  <Badge 
                    variant={selectedProfile === profile.id ? "secondary" : "outline"}
                    className="text-xs"
                  >
                    {profile.recordCount.toLocaleString()}
                  </Badge>
                </div>
              )}
            </Button>
          ))}
        </div>
        
        {/* Profile Info Summary */}
        {profilesInfo && (
          <div className="mt-4 pt-3 border-t text-xs text-muted-foreground">
            <p>
              {profileOptions.length} profiles found, {Object.keys(profilesInfo.profiles).length} configured
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
})

ProfileSelector.displayName = 'ProfileSelector'