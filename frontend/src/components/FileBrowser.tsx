import { Folder, File, Home, Download, ChevronRight, DownloadCloud, Power } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import type { FileItem } from '@/types'
import { api } from '@/lib/api'

interface FileBrowserProps {
  files: FileItem[]
  currentPath: string
  currentDevice: string | null
  onNavigate: (path: string) => void
  onExtractAll: () => void
  onUnmount: () => void
}

export function FileBrowser({
  files,
  currentPath,
  currentDevice,
  onNavigate,
  onExtractAll,
  onUnmount,
}: FileBrowserProps) {
  const breadcrumbs = currentPath.split('/').filter(Boolean)

  const handleFileClick = (file: FileItem) => {
    if (file.type === 'dir') {
      const newPath = currentPath === '/' ? `/${file.name}` : `${currentPath}/${file.name}`
      onNavigate(newPath)
    }
  }

  const handleBreadcrumbClick = (index: number) => {
    if (index === -1) {
      onNavigate('/')
    } else {
      const newPath = '/' + breadcrumbs.slice(0, index + 1).join('/')
      onNavigate(newPath)
    }
  }

  if (!currentDevice) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Folder className="h-5 w-5" />
            Files
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-32">
            <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <Folder className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-lg font-semibold text-muted-foreground">No Device Connected</p>
            <p className="text-sm text-muted-foreground mt-2">Select a device to browse files</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Folder className="h-5 w-5" />
            Files
          </CardTitle>
          <div className="flex gap-2">
            <Button onClick={onExtractAll} variant="default" size="sm">
              <DownloadCloud className="h-4 w-4" />
              Download All
            </Button>
            <Button onClick={onUnmount} variant="outline" size="sm">
              <Power className="h-4 w-4" />
              Eject
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Breadcrumbs */}
        <div className="flex items-center gap-2 mb-4 pb-4 border-b flex-wrap">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleBreadcrumbClick(-1)}
            className="h-8"
          >
            <Home className="h-4 w-4" />
            Home
          </Button>
          {breadcrumbs.map((crumb, index) => (
            <div key={index} className="flex items-center gap-2">
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
              <Button
                variant={index === breadcrumbs.length - 1 ? "secondary" : "ghost"}
                size="sm"
                onClick={() => handleBreadcrumbClick(index)}
                className="h-8"
              >
                {crumb}
              </Button>
            </div>
          ))}
        </div>

        {/* File List */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {files.length === 0 ? (
            <div className="col-span-2 text-center py-12">
              <p className="text-sm text-muted-foreground">Empty directory</p>
            </div>
          ) : (
            files.map((file) => (
              <div
                key={file.path}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors group"
              >
                <div
                  className={`flex items-center gap-3 flex-1 ${
                    file.type === 'dir' ? 'cursor-pointer' : ''
                  }`}
                  onClick={() => handleFileClick(file)}
                >
                  <div className="p-2 bg-muted rounded-md">
                    {file.type === 'dir' ? (
                      <Folder className="h-5 w-5 text-blue-600" />
                    ) : (
                      <File className="h-5 w-5 text-muted-foreground" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{file.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {file.type === 'dir' ? 'Folder' : file.size} • {file.modified}
                    </div>
                  </div>
                </div>
                {file.type === 'file' && currentDevice && (
                  <a
                    href={api.getDownloadUrl(
                      currentDevice,
                      (currentPath === '/' ? '/' : currentPath + '/') + file.name
                    )}
                    download
                  >
                    <Button
                      variant="ghost"
                      size="icon"
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </a>
                )}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
