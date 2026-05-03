import { HardDrive, ChevronRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { Device } from '@/types'

interface DeviceListProps {
  devices: Device[]
  onMountDevice: (devicePath: string) => void
}

export function DeviceList({ devices, onMountDevice }: DeviceListProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <HardDrive className="h-5 w-5" />
          Devices
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {devices.length === 0 ? (
          <div className="text-center py-12">
            <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-3">
              <HardDrive className="h-6 w-6 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground">No devices found</p>
          </div>
        ) : (
          devices.map((device) => (
            <Button
              key={device.path}
              variant={device.mounted ? "default" : "outline"}
              className="w-full h-auto p-4 justify-between"
              onClick={() => !device.mounted && onMountDevice(device.path)}
              disabled={device.mounted}
            >
              <div className="flex items-center gap-3 text-left">
                <div className={`p-2 rounded-md ${device.mounted ? 'bg-primary-foreground/20' : 'bg-muted'}`}>
                  <HardDrive className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <div className="font-semibold">{device.label}</div>
                  <div className="text-xs opacity-80">{device.name}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="secondary" className="text-xs">
                      {device.size}
                    </Badge>
                    <span className="text-xs opacity-60">{device.path}</span>
                  </div>
                </div>
              </div>
              {!device.mounted && <ChevronRight className="h-4 w-4" />}
            </Button>
          ))
        )}
      </CardContent>
    </Card>
  )
}
