import apiClient, { apiBaseUrl, unwrapResponse } from './http'
import type { ExcelExportCreatePayload, ExportCreatePayload, ExportJob } from '@/types/domain'

export async function createProjectExport(projectId: string, payload: ExportCreatePayload = { format: 'txt' }) {
  return unwrapResponse<ExportJob>(apiClient.post(`/projects/${projectId}/export`, payload))
}

export async function createProjectExcelExport(projectId: string, payload: ExcelExportCreatePayload) {
  return unwrapResponse<ExportJob>(apiClient.post(`/projects/${projectId}/export-excel`, payload))
}

export async function listProjectExports(projectId: string) {
  return unwrapResponse<ExportJob[]>(apiClient.get(`/projects/${projectId}/export-jobs`))
}

export function getExportDownloadUrl(exportId: string) {
  return `${apiBaseUrl.replace(/\/$/, '')}/exports/${exportId}/download`
}
