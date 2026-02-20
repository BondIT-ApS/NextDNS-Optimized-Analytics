import { useCallback, useEffect, useState } from 'react'
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
  Key,
  Layers,
  Settings as SettingsIcon,
  Trash2,
  Plus,
  Eye,
  EyeOff,
  RefreshCw,
  Save,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react'
import { apiClient } from '@/services/api'
import type { SettingsProfileItem, SystemSettingsResponse } from '@/types/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ApiKeyState {
  masked: string
  configured: boolean
  loading: boolean
  editing: boolean
  inputValue: string
  saving: boolean
  error: string | null
  success: string | null
}

interface ProfilesState {
  profiles: SettingsProfileItem[]
  profileNames: Record<string, string>
  loading: boolean
  error: string | null
  addInput: string
  adding: boolean
  addError: string | null
}

interface SystemState {
  settings: SystemSettingsResponse | null
  loading: boolean
  saving: boolean
  error: string | null
  success: string | null
  fetchInterval: string
  fetchLimit: string
  logLevel: string
}

const LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] as const

// ---------------------------------------------------------------------------
// NextDNS API Key card
// ---------------------------------------------------------------------------

function ApiKeyCard() {
  const [state, setState] = useState<ApiKeyState>({
    masked: '',
    configured: false,
    loading: true,
    editing: false,
    inputValue: '',
    saving: false,
    error: null,
    success: null,
  })
  const [showInput, setShowInput] = useState(false)

  const load = useCallback(async () => {
    setState(s => ({ ...s, loading: true, error: null }))
    try {
      const data = await apiClient.getNextDNSApiKey()
      setState(s => ({
        ...s,
        masked: data.masked_key ?? '',
        configured: data.configured,
        loading: false,
      }))
    } catch {
      setState(s => ({ ...s, loading: false, error: 'Failed to load API key' }))
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleSave = async () => {
    if (!state.inputValue.trim()) return
    setState(s => ({ ...s, saving: true, error: null, success: null }))
    try {
      const data = await apiClient.updateNextDNSApiKey(state.inputValue.trim())
      setState(s => ({
        ...s,
        masked: data.masked_key ?? '',
        configured: data.configured,
        saving: false,
        editing: false,
        inputValue: '',
        success: 'API key updated successfully',
      }))
      setTimeout(() => setState(s => ({ ...s, success: null })), 3000)
    } catch (err: unknown) {
      const detail =
        err &&
        typeof err === 'object' &&
        'data' in err &&
        err.data &&
        typeof err.data === 'object' &&
        'detail' in err.data
          ? String((err.data as { detail: string }).detail)
          : 'Failed to update API key'
      setState(s => ({ ...s, saving: false, error: detail }))
    }
  }

  const handleCancel = () => {
    setState(s => ({
      ...s,
      editing: false,
      inputValue: '',
      error: null,
    }))
    setShowInput(false)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Key className="h-5 w-5 text-lego-blue" />
            <CardTitle>NextDNS API Key</CardTitle>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={load}
            disabled={state.loading}
          >
            <RefreshCw
              className={`h-4 w-4 ${state.loading ? 'animate-spin' : ''}`}
            />
          </Button>
        </div>
        <CardDescription>
          The API key used to fetch DNS logs from NextDNS. Changes take effect
          on the next scheduler cycle.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current key display */}
        <div className="flex items-center gap-3">
          <div className="flex-1 rounded-md border bg-muted px-3 py-2 font-mono text-sm">
            {state.loading ? (
              <span className="text-muted-foreground">Loading…</span>
            ) : state.configured ? (
              state.masked
            ) : (
              <span className="text-muted-foreground italic">
                Not configured
              </span>
            )}
          </div>
          {state.configured && (
            <Badge variant="secondary" className="text-lego-green shrink-0">
              Configured
            </Badge>
          )}
        </div>

        {/* Edit form */}
        {state.editing ? (
          <div className="space-y-2">
            <div className="relative flex items-center gap-2">
              <Input
                type={showInput ? 'text' : 'password'}
                placeholder="Enter new API key"
                value={state.inputValue}
                onChange={e =>
                  setState(s => ({ ...s, inputValue: e.target.value }))
                }
                onKeyDown={e => e.key === 'Enter' && handleSave()}
                disabled={state.saving}
                className="flex-1 font-mono"
                autoFocus
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setShowInput(v => !v)}
                className="shrink-0"
              >
                {showInput ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
            {state.error && (
              <p className="text-sm text-destructive">{state.error}</p>
            )}
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={handleSave}
                disabled={state.saving || !state.inputValue.trim()}
              >
                <Save className="mr-1 h-3 w-3" />
                {state.saving ? 'Saving…' : 'Save'}
              </Button>
              <Button size="sm" variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <Button
              size="sm"
              variant="outline"
              onClick={() =>
                setState(s => ({ ...s, editing: true, error: null }))
              }
            >
              {state.configured ? 'Update API Key' : 'Set API Key'}
            </Button>
            {state.success && (
              <span className="text-sm text-lego-green">{state.success}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Profile Management card
// ---------------------------------------------------------------------------

function ProfilesCard() {
  const [state, setState] = useState<ProfilesState>({
    profiles: [],
    profileNames: {},
    loading: true,
    error: null,
    addInput: '',
    adding: false,
    addError: null,
  })

  const load = useCallback(async () => {
    setState(s => ({ ...s, loading: true, error: null }))
    try {
      const [profilesData, infoData] = await Promise.all([
        apiClient.getNextDNSProfiles(),
        apiClient.getProfilesInfo().catch(() => null),
      ])
      const names: Record<string, string> = {}
      if (infoData) {
        Object.entries(infoData.profiles).forEach(([id, info]) => {
          if (info.name) names[id] = info.name
        })
      }
      setState(s => ({
        ...s,
        profiles: profilesData.profiles,
        profileNames: names,
        loading: false,
      }))
    } catch {
      setState(s => ({
        ...s,
        loading: false,
        error: 'Failed to load profiles',
      }))
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleToggle = async (profile: SettingsProfileItem) => {
    try {
      const updated = await apiClient.updateNextDNSProfile(
        profile.profile_id,
        !profile.enabled
      )
      setState(s => ({
        ...s,
        profiles: s.profiles.map(p =>
          p.profile_id === updated.profile_id ? updated : p
        ),
      }))
    } catch {
      setState(s => ({
        ...s,
        error: `Failed to update profile ${profile.profile_id}`,
      }))
    }
  }

  const handleDelete = async (profileId: string) => {
    const purge = window.confirm(
      `Delete profile "${profileId}"?\n\nClick OK to also delete all DNS logs for this profile, or Cancel to keep the data.`
    )
    // If they cancelled the confirm, bail out entirely
    if (purge === null) return

    try {
      await apiClient.deleteNextDNSProfile(profileId, purge)
      setState(s => ({
        ...s,
        profiles: s.profiles.filter(p => p.profile_id !== profileId),
      }))
    } catch {
      setState(s => ({ ...s, error: `Failed to delete profile ${profileId}` }))
    }
  }

  const handleAdd = async () => {
    const id = state.addInput.trim()
    if (!id) return
    setState(s => ({ ...s, adding: true, addError: null }))
    try {
      const added = await apiClient.addNextDNSProfile(id)
      setState(s => ({
        ...s,
        adding: false,
        addInput: '',
        profiles: [
          ...s.profiles,
          {
            profile_id: added.profile_id,
            enabled: added.enabled,
            created_at: null,
            updated_at: null,
          },
        ],
      }))
    } catch (err: unknown) {
      const detail =
        err &&
        typeof err === 'object' &&
        'data' in err &&
        err.data &&
        typeof err.data === 'object' &&
        'detail' in err.data
          ? String((err.data as { detail: string }).detail)
          : `Failed to add profile "${id}"`
      setState(s => ({ ...s, adding: false, addError: detail }))
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-lego-blue" />
            <CardTitle>Profile Management</CardTitle>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={load}
            disabled={state.loading}
          >
            <RefreshCw
              className={`h-4 w-4 ${state.loading ? 'animate-spin' : ''}`}
            />
          </Button>
        </div>
        <CardDescription>
          Manage the NextDNS profiles whose logs are fetched and stored.
          Disabled profiles are skipped during fetch cycles.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {state.error && (
          <p className="text-sm text-destructive">{state.error}</p>
        )}

        {/* Profile list */}
        {state.loading ? (
          <p className="text-sm text-muted-foreground">Loading profiles…</p>
        ) : state.profiles.length === 0 ? (
          <p className="text-sm text-muted-foreground italic">
            No profiles configured yet.
          </p>
        ) : (
          <div className="space-y-2">
            {state.profiles.map(profile => (
              <div
                key={profile.profile_id}
                className="flex items-center justify-between rounded-md border px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">
                    {state.profileNames[profile.profile_id]
                      ? `${state.profileNames[profile.profile_id]} (${profile.profile_id})`
                      : profile.profile_id}
                  </span>
                  <Badge
                    variant={profile.enabled ? 'default' : 'secondary'}
                    className={
                      profile.enabled
                        ? 'bg-lego-green text-white'
                        : 'text-muted-foreground'
                    }
                  >
                    {profile.enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggle(profile)}
                    title={
                      profile.enabled ? 'Disable profile' : 'Enable profile'
                    }
                  >
                    {profile.enabled ? (
                      <ToggleRight className="h-4 w-4 text-lego-green" />
                    ) : (
                      <ToggleLeft className="h-4 w-4 text-muted-foreground" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(profile.profile_id)}
                    title="Delete profile"
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Add profile form */}
        <div className="border-t pt-4">
          <p className="mb-2 text-sm font-medium text-foreground">
            Add Profile
          </p>
          <div className="flex items-center gap-2">
            <Input
              placeholder="NextDNS profile ID (e.g. abc123)"
              value={state.addInput}
              onChange={e =>
                setState(s => ({
                  ...s,
                  addInput: e.target.value,
                  addError: null,
                }))
              }
              onKeyDown={e => e.key === 'Enter' && handleAdd()}
              disabled={state.adding}
              className="font-mono"
            />
            <Button
              size="sm"
              onClick={handleAdd}
              disabled={state.adding || !state.addInput.trim()}
            >
              <Plus className="mr-1 h-3 w-3" />
              {state.adding ? 'Adding…' : 'Add'}
            </Button>
          </div>
          {state.addError && (
            <p className="mt-1 text-sm text-destructive">{state.addError}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// System Settings card
// ---------------------------------------------------------------------------

function SystemSettingsCard() {
  const [state, setState] = useState<SystemState>({
    settings: null,
    loading: true,
    saving: false,
    error: null,
    success: null,
    fetchInterval: '',
    fetchLimit: '',
    logLevel: 'INFO',
  })

  const load = useCallback(async () => {
    setState(s => ({ ...s, loading: true, error: null }))
    try {
      const data = await apiClient.getSystemSettings()
      setState(s => ({
        ...s,
        settings: data,
        loading: false,
        fetchInterval: String(data.fetch_interval),
        fetchLimit: String(data.fetch_limit),
        logLevel: data.log_level,
      }))
    } catch {
      setState(s => ({
        ...s,
        loading: false,
        error: 'Failed to load system settings',
      }))
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleSave = async () => {
    const interval = parseInt(state.fetchInterval, 10)
    const limit = parseInt(state.fetchLimit, 10)

    if (isNaN(interval) || interval < 1 || interval > 1440) {
      setState(s => ({
        ...s,
        error: 'Fetch interval must be between 1 and 1440 minutes',
      }))
      return
    }
    if (isNaN(limit) || limit < 10 || limit > 1000) {
      setState(s => ({
        ...s,
        error: 'Fetch limit must be between 10 and 1000',
      }))
      return
    }

    setState(s => ({ ...s, saving: true, error: null, success: null }))
    try {
      const updated = await apiClient.updateSystemSettings({
        fetch_interval: interval,
        fetch_limit: limit,
        log_level: state.logLevel,
      })
      setState(s => ({
        ...s,
        settings: updated,
        saving: false,
        fetchInterval: String(updated.fetch_interval),
        fetchLimit: String(updated.fetch_limit),
        logLevel: updated.log_level,
        success: 'Settings saved — changes are now active',
      }))
      setTimeout(() => setState(s => ({ ...s, success: null })), 4000)
    } catch (err: unknown) {
      const detail =
        err &&
        typeof err === 'object' &&
        'data' in err &&
        err.data &&
        typeof err.data === 'object' &&
        'detail' in err.data
          ? String((err.data as { detail: string }).detail)
          : 'Failed to save settings'
      setState(s => ({ ...s, saving: false, error: detail }))
    }
  }

  const isDirty =
    state.settings !== null &&
    (state.fetchInterval !== String(state.settings.fetch_interval) ||
      state.fetchLimit !== String(state.settings.fetch_limit) ||
      state.logLevel !== state.settings.log_level)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <SettingsIcon className="h-5 w-5 text-lego-blue" />
            <CardTitle>System Settings</CardTitle>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={load}
            disabled={state.loading}
          >
            <RefreshCw
              className={`h-4 w-4 ${state.loading ? 'animate-spin' : ''}`}
            />
          </Button>
        </div>
        <CardDescription>
          Scheduler behaviour and application logging. All changes apply
          immediately — no restart required.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {state.loading ? (
          <p className="text-sm text-muted-foreground">Loading settings…</p>
        ) : (
          <>
            {/* Fetch Interval */}
            <div className="space-y-1">
              <label className="text-sm font-medium" htmlFor="fetch-interval">
                Fetch Interval
              </label>
              <p className="text-xs text-muted-foreground">
                How often the scheduler polls NextDNS for new logs (1–1440
                minutes).
              </p>
              <div className="flex items-center gap-2">
                <Input
                  id="fetch-interval"
                  type="number"
                  min={1}
                  max={1440}
                  value={state.fetchInterval}
                  onChange={e =>
                    setState(s => ({
                      ...s,
                      fetchInterval: e.target.value,
                      error: null,
                    }))
                  }
                  className="w-32"
                />
                <span className="text-sm text-muted-foreground">minutes</span>
              </div>
            </div>

            {/* Fetch Limit */}
            <div className="space-y-1">
              <label className="text-sm font-medium" htmlFor="fetch-limit">
                Fetch Limit
              </label>
              <p className="text-xs text-muted-foreground">
                Maximum DNS log records fetched per API request (10–1000).
              </p>
              <div className="flex items-center gap-2">
                <Input
                  id="fetch-limit"
                  type="number"
                  min={10}
                  max={1000}
                  value={state.fetchLimit}
                  onChange={e =>
                    setState(s => ({
                      ...s,
                      fetchLimit: e.target.value,
                      error: null,
                    }))
                  }
                  className="w-32"
                />
                <span className="text-sm text-muted-foreground">records</span>
              </div>
            </div>

            {/* Log Level */}
            <div className="space-y-1">
              <label className="text-sm font-medium" htmlFor="log-level">
                Log Level
              </label>
              <p className="text-xs text-muted-foreground">
                Backend logging verbosity. DEBUG produces the most output.
              </p>
              <select
                id="log-level"
                value={state.logLevel}
                onChange={e =>
                  setState(s => ({
                    ...s,
                    logLevel: e.target.value,
                    error: null,
                  }))
                }
                className="h-9 w-40 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              >
                {LOG_LEVELS.map(level => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
            </div>

            {/* Actions */}
            {state.error && (
              <p className="text-sm text-destructive">{state.error}</p>
            )}
            <div className="flex items-center gap-3 border-t pt-4">
              <Button onClick={handleSave} disabled={state.saving || !isDirty}>
                <Save className="mr-1 h-4 w-4" />
                {state.saving ? 'Saving…' : 'Save Settings'}
              </Button>
              {state.success && (
                <span className="text-sm text-lego-green">{state.success}</span>
              )}
              {isDirty && !state.saving && (
                <span className="text-xs text-muted-foreground">
                  Unsaved changes
                </span>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Main Settings page
// ---------------------------------------------------------------------------

export function Settings() {
  return (
    <div className="space-y-6">
      <ApiKeyCard />
      <ProfilesCard />
      <SystemSettingsCard />
    </div>
  )
}

export default Settings
