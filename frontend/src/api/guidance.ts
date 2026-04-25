import apiClient, { unwrapResponse } from './http'
import type {
  GuidanceHistoryLinkResult,
  GuidanceHistoryMatch,
  GuidanceImportResult,
  GuidanceItem,
  GuidanceLibrary,
  GuidanceSearchResult,
} from '@/types/domain'

export async function importGuidanceMarkdown() {
  return unwrapResponse<GuidanceImportResult>(apiClient.post('/guidance/import-md'))
}

export async function listGuidanceItems(keyword?: string) {
  return unwrapResponse<GuidanceLibrary>(apiClient.get('/guidance/items', { params: keyword ? { keyword } : undefined }))
}

export async function getGuidanceItem(guidanceId: string) {
  return unwrapResponse<GuidanceItem>(apiClient.get(`/guidance/items/${guidanceId}`))
}

export async function searchGuidanceItems(keyword: string) {
  return unwrapResponse<GuidanceSearchResult>(apiClient.get('/guidance/search', { params: { keyword } }))
}

export async function linkGuidanceHistory(guidanceId: string) {
  return unwrapResponse<GuidanceHistoryLinkResult>(apiClient.post(`/guidance/${guidanceId}/link-history`))
}

export async function listGuidanceHistoryRecords(guidanceId: string, complianceStatus?: string) {
  return unwrapResponse<GuidanceHistoryMatch[]>(
    apiClient.get(`/guidance/${guidanceId}/history-records`, {
      params: complianceStatus ? { compliance_status: complianceStatus } : undefined,
    }),
  )
}
