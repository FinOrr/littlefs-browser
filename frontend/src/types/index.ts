export interface Device {
  path: string
  name: string
  size: string
  label: string
  mounted: boolean
}

export interface FileItem {
  name: string
  type: 'file' | 'dir'
  size: string
  modified: string
  path: string
}

export interface MountResponse {
  success: boolean
  mount_point?: string
  params?: Record<string, number>
  error?: string
}

export interface ListResponse {
  success: boolean
  items?: FileItem[]
  path?: string
  error?: string
}

export interface ExtractResponse {
  success: boolean
  destination?: string
  fileCount?: string
  totalSize?: string
  error?: string
}
