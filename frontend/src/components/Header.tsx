import { RefreshCw, HardDrive } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ThemeToggle } from '@/components/ThemeToggle'

interface HeaderProps {
  onScanDevices: () => void
  isScanning: boolean
  status: string
  isConnected: boolean
}

export function Header({ onScanDevices, isScanning, status, isConnected }: HeaderProps) {
  return (
    <div className="border-b bg-card">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary rounded-lg">
              <HardDrive className="h-6 w-6 text-primary-foreground" />
            </div>
            <h1 className="text-2xl font-bold">LittleFS Browser</h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-slate-300'}`} />
              <span className="text-sm text-muted-foreground">{status}</span>
              <Badge variant="secondary" className="ml-2">
                {isConnected ? 'Connected' : 'Ready'}
              </Badge>
            </div>

            <ThemeToggle />

            <Button onClick={onScanDevices} disabled={isScanning}>
              <RefreshCw className={isScanning ? 'animate-spin' : ''} />
              Scan Devices
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
