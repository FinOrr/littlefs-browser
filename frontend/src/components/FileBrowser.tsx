import { Folder, File, Home, Download, ChevronRight, DownloadCloud, Power, Trash2, Eye, Trash } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogClose } from '@/components/ui/dialog'
import type { FileItem } from '@/types'
import { api } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { useState } from 'react'

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
  const { toast } = useToast()
  const breadcrumbs = currentPath.split('/').filter(Boolean)
  const [previewFile, setPreviewFile] = useState<FileItem | null>(null)
  const [previewContent, setPreviewContent] = useState<string>('')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [isText, setIsText] = useState(true)
  const [isTruncated, setIsTruncated] = useState(false)

  const handleFileClick = async (file: FileItem) => {
    if (file.type === 'dir') {
      const newPath = currentPath === '/' ? `/${file.name}` : `${currentPath}/${file.name}`
      onNavigate(newPath)
    } else {
      // Preview file
      if (!currentDevice) return
      setPreviewFile(file)
      setPreviewLoading(true)
      try {
        const targetPath = (currentPath === '/' ? '/' : currentPath + '/') + file.name
        const result = await api.previewFile(currentDevice, targetPath)
        if (result.success && result.content !== undefined) {
          setPreviewContent(result.content)
          setIsText(result.is_text ?? true)
          setIsTruncated(result.truncated ?? false)
        } else {
          toast({ title: 'Preview Failed', description: result.error || 'Unknown error', variant: 'destructive' })
          setPreviewFile(null)
        }
      } catch (e) {
        toast({ title: 'Error', description: 'Failed to preview file', variant: 'destructive' })
        setPreviewFile(null)
      } finally {
        setPreviewLoading(false)
      }
    }
  }

  const handleDelete = async (file: FileItem) => {
    if (!currentDevice) return
    const targetPath = (currentPath === '/' ? '/' : currentPath + '/') + file.name
    const itemType = file.type === 'dir' ? 'folder' : 'file'
    const confirmed = window.confirm(`Delete ${itemType} "${file.name}"? This cannot be undone.`)
    if (!confirmed) return
    try {
      const result = await api.deleteFile(currentDevice, targetPath)
      if (result.success) {
        toast({ title: 'Deleted', description: `${file.name} removed` })
        onNavigate(currentPath)
      } else {
        toast({ title: 'Delete Failed', description: result.error || 'Unknown error', variant: 'destructive' })
      }
    } catch (e) {
      toast({ title: 'Error', description: `Failed to delete ${itemType}`, variant: 'destructive' })
    }
  }

  const handleDeleteAll = async () => {
    if (!currentDevice) return
    const itemCount = files.length
    if (itemCount === 0) {
      toast({ title: 'Nothing to Delete', description: 'Directory is already empty' })
      return
    }
    const confirmed = window.confirm(
      `Delete ALL ${itemCount} items in this directory? This cannot be undone.`
    )
    if (!confirmed) return
    try {
      const result = await api.deleteAll(currentDevice, currentPath)
      if (result.success) {
        toast({ 
          title: 'All Deleted', 
          description: `Removed ${result.deleted_count} items` 
        })
        onNavigate(currentPath)
      } else {
        toast({ 
          title: 'Delete Failed', 
          description: result.error || 'Unknown error', 
          variant: 'destructive' 
        })
      }
    } catch (e) {
      toast({ title: 'Error', description: 'Failed to delete all items', variant: 'destructive' })
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
            <Button 
              onClick={handleDeleteAll} 
              variant="destructive" 
              size="sm"
              disabled={files.length === 0}
            >
              <Trash className="h-4 w-4" />
              Delete All
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
                  className="flex items-center gap-3 flex-1 cursor-pointer"
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
                {currentDevice && (
                  <div className="flex items-center gap-1">
                    {file.type === 'file' && (
                      <>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleFileClick(file)
                          }}
                          className="opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Preview"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <a
                          href={api.getDownloadUrl(
                            currentDevice,
                            (currentPath === '/' ? '/' : currentPath + '/') + file.name
                          )}
                          download
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Button
                            variant="ghost"
                            size="icon"
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                            title="Download"
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                        </a>
                      </>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete(file)
                      }}
                      className="opacity-0 group-hover:opacity-100 transition-opacity text-red-600 hover:text-red-700"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </CardContent>

      {/* Preview Modal */}
      <Dialog open={previewFile !== null} onOpenChange={(open) => !open && setPreviewFile(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{previewFile?.name}</DialogTitle>
            <DialogClose onClose={() => setPreviewFile(null)} />
          </DialogHeader>
          <div className="p-6 overflow-auto max-h-[60vh]">
            {previewLoading ? (
              <div className="text-center py-8 text-muted-foreground">Loading preview...</div>
            ) : isText ? (
              <>
                <pre className="text-sm font-mono bg-muted p-4 rounded-lg overflow-auto whitespace-pre-wrap break-words">
                  {previewContent}
                </pre>
                {isTruncated && (
                  <p className="text-sm text-amber-600 mt-2">
                    ⚠ File truncated (showing first 1MB)
                  </p>
                )}
              </>
            ) : (
              <>
                <div className="text-sm font-mono bg-muted p-4 rounded-lg overflow-auto">
                  <div className="text-muted-foreground mb-2">Binary file (hex view):</div>
                  <div className="break-all">{previewContent}</div>
                </div>
                {isTruncated && (
                  <p className="text-sm text-amber-600 mt-2">
                    ⚠ File truncated (showing first 1MB)
                  </p>
                )}
              </>
            )}
          </div>
          <div className="flex justify-end gap-2 p-6 pt-0">
            {previewFile && currentDevice && (
              <a
                href={api.getDownloadUrl(
                  currentDevice,
                  (currentPath === '/' ? '/' : currentPath + '/') + previewFile.name
                )}
                download
              >
                <Button variant="default">
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
              </a>
            )}
            <Button variant="outline" onClick={() => setPreviewFile(null)}>
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
