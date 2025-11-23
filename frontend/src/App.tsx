import { useState, useEffect } from 'react'
import { Header } from '@/components/Header'
import { DeviceList } from '@/components/DeviceList'
import { FileBrowser } from '@/components/FileBrowser'
import { InfoCard } from '@/components/InfoCard'
import { Toaster } from '@/components/ui/toaster'
import { useToast } from '@/hooks/use-toast'
import { api } from '@/lib/api'
import type { Device, FileItem } from '@/types'
import { Copy } from 'lucide-react'
import { Button } from '@/components/ui/button'

function App() {
  const [devices, setDevices] = useState<Device[]>([])
  const [currentDevice, setCurrentDevice] = useState<string | null>(null)
  const [currentPath, setCurrentPath] = useState<string>('/')
  const [files, setFiles] = useState<FileItem[]>([])
  const [isScanning, setIsScanning] = useState(false)
  const [status, setStatus] = useState('Ready')
  const { toast } = useToast()

  const scanDevices = async () => {
    setIsScanning(true)
    setStatus('Scanning...')
    try {
      const deviceList = await api.getDevices()
      setDevices(deviceList)
      setStatus('Ready')
    } catch (error) {
      console.error('Failed to scan devices:', error)
      setStatus('Error')
      toast({
        title: 'Scan Failed',
        description: 'Failed to scan for devices',
        variant: 'destructive',
      })
    } finally {
      setIsScanning(false)
    }
  }

  const mountDevice = async (devicePath: string) => {
    setStatus('Mounting...')
    try {
      const result = await api.mountDevice(devicePath)
      if (result.success) {
        setCurrentDevice(devicePath)
        setCurrentPath('/')
        setStatus('Connected')
        await scanDevices()
        await loadFiles(devicePath, '/')
        toast({
          title: 'Device Mounted',
          description: `Successfully mounted ${devicePath.split('/').pop()}`,
        })
      } else {
        setStatus('Mount failed')
        toast({
          title: 'Mount Failed',
          description: result.error || 'Unknown error',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Failed to mount device:', error)
      setStatus('Error')
      toast({
        title: 'Mount Error',
        description: 'An unexpected error occurred',
        variant: 'destructive',
      })
    }
  }

  const unmountDevice = async () => {
    if (!currentDevice) return

    setStatus('Ejecting...')
    try {
      const result = await api.unmountDevice(currentDevice)
      if (result.success) {
        setCurrentDevice(null)
        setCurrentPath('/')
        setFiles([])
        setStatus('Ready')
        await scanDevices()
        toast({
          title: 'Device Ejected',
          description: 'Device successfully unmounted',
        })
      } else {
        setStatus('Eject failed')
        toast({
          title: 'Eject Failed',
          description: result.error || 'Unknown error',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Failed to unmount device:', error)
      setStatus('Error')
      toast({
        title: 'Eject Error',
        description: 'An unexpected error occurred',
        variant: 'destructive',
      })
    }
  }

  const loadFiles = async (device: string, path: string) => {
    try {
      const result = await api.listFiles(device, path)
      if (result.success && result.items) {
        setFiles(result.items)
      } else {
        toast({
          title: 'Failed to Load Files',
          description: result.error || 'Unknown error',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Failed to load files:', error)
      toast({
        title: 'Error',
        description: 'Failed to load directory contents',
        variant: 'destructive',
      })
    }
  }

  const handleNavigate = (path: string) => {
    if (currentDevice) {
      setCurrentPath(path)
      loadFiles(currentDevice, path)
    }
  }

  const handleExtractAll = async () => {
    if (!currentDevice) return

    setStatus('Downloading...')
    try {
      const result = await api.extractAll(currentDevice)
      if (result.success) {
        setStatus('Connected')
        toast({
          title: 'Download Complete!',
          description: (
            <div className="space-y-3">
              <p>All files successfully extracted</p>
              <div className="bg-muted p-3 rounded-md space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Files Extracted:</span>
                  <span className="font-semibold">{result.fileCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Size:</span>
                  <span className="font-semibold">{result.totalSize}</span>
                </div>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-2">Location:</p>
                <div className="bg-muted px-3 py-2 rounded-md font-mono text-xs break-all">
                  {result.destination}
                </div>
              </div>
              <Button
                size="sm"
                className="w-full mt-2"
                onClick={() => {
                  navigator.clipboard.writeText(result.destination || '')
                  toast({
                    title: 'Copied!',
                    description: 'Path copied to clipboard',
                  })
                }}
              >
                <Copy className="h-3 w-3 mr-2" />
                Copy Path
              </Button>
            </div>
          ),
        })
      } else {
        setStatus('Download failed')
        toast({
          title: 'Download Failed',
          description: result.error || 'Unknown error',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Failed to extract files:', error)
      setStatus('Error')
      toast({
        title: 'Error',
        description: 'An unexpected error occurred',
        variant: 'destructive',
      })
    }
  }

  useEffect(() => {
    scanDevices()
  }, [])

  return (
    <div className="min-h-screen bg-background">
      <Header
        onScanDevices={scanDevices}
        isScanning={isScanning}
        status={status}
        isConnected={!!currentDevice}
      />

      <div className="container mx-auto px-6 py-6">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Left Column - Devices */}
          <div className="xl:col-span-1 space-y-6">
            <DeviceList devices={devices} onMountDevice={mountDevice} />
            <InfoCard deviceCount={devices.length} mounted={!!currentDevice} />
          </div>

          {/* Right Column - File Browser */}
          <div className="xl:col-span-2">
            <FileBrowser
              files={files}
              currentPath={currentPath}
              currentDevice={currentDevice}
              onNavigate={handleNavigate}
              onExtractAll={handleExtractAll}
              onUnmount={unmountDevice}
            />
          </div>
        </div>
      </div>

      <Toaster />
    </div>
  )
}

export default App
