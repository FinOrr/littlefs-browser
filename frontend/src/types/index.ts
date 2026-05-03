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

export interface DeleteResponse {
  success: boolean
  error?: string
}

export interface PreviewResponse {
  success: boolean
  content?: string
  is_text?: boolean
  size?: number
  truncated?: boolean
  filename?: string
  error?: string
}

export interface DeleteAllResponse {
  success: boolean
  deleted_count?: number
  error?: string
  details?: string[]
}
