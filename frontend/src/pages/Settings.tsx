import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Settings as SettingsIcon } from 'lucide-react'

export function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground">
          System configuration and preferences
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <SettingsIcon className="h-5 w-5 text-lego-blue" />
            Configuration Panel
          </CardTitle>
          <CardDescription>
            System settings and user preferences
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            🧱 Configuration settings coming soon! This will include system
            preferences, API configuration, and user customization options.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

export default Settings
