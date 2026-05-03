import type { Device, MountResponse, ListResponse, ExtractResponse, DeleteResponse, PreviewResponse, DeleteAllResponse } from '@/types'

const API_BASE = '/api'

export const api = {
  async getDevices(): Promise<Device[]> {
    const response = await fetch(`${API_BASE}/devices`)
    return response.json()
  },

  async mountDevice(devicePath: string): Promise<MountResponse> {
    const response = await fetch(`${API_BASE}/mount`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device: devicePath }),
    })
    return response.json()
  },

  async unmountDevice(devicePath: string): Promise<{ success: boolean; error?: string }> {
    const response = await fetch(`${API_BASE}/unmount`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device: devicePath }),
    })
    return response.json()
  },

  async listFiles(devicePath: string, path: string = '/'): Promise<ListResponse> {
    const response = await fetch(
      `${API_BASE}/list?device=${encodeURIComponent(devicePath)}&path=${encodeURIComponent(path)}`
    )
    return response.json()
  },

  async extractAll(devicePath: string, destination?: string): Promise<ExtractResponse> {
    const response = await fetch(`${API_BASE}/extract-all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device: devicePath, destination }),
    })
    return response.json()
  },

  getDownloadUrl(devicePath: string, filePath: string): string {
    return `${API_BASE}/download?device=${encodeURIComponent(devicePath)}&path=${encodeURIComponent(filePath)}`
  },

  async deleteFile(devicePath: string, filePath: string): Promise<DeleteResponse> {
    const response = await fetch(
      `${API_BASE}/delete?device=${encodeURIComponent(devicePath)}&path=${encodeURIComponent(filePath)}`,
      { method: 'DELETE' }
    )
    return response.json()
  },

  async previewFile(devicePath: string, filePath: string): Promise<PreviewResponse> {
    const response = await fetch(
      `${API_BASE}/preview?device=${encodeURIComponent(devicePath)}&path=${encodeURIComponent(filePath)}`
    )
    return response.json()
  },

  async deleteAll(devicePath: string, dirPath: string = '/'): Promise<DeleteAllResponse> {
    const response = await fetch(
      `${API_BASE}/delete-all?device=${encodeURIComponent(devicePath)}&path=${encodeURIComponent(dirPath)}`,
      { method: 'DELETE' }
    )
    return response.json()
  },
}
