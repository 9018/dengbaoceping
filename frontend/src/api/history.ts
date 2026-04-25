import apiClient, { unwrapResponse } from './http'
import type {
  HistoryImportResult,
  HistoryPhraseSummary,
  HistoryRecord,
  HistorySimilarRecord,
  HistoryStats,
} from '@/types/domain'

export interface HistoryRecordFilters {
  asset_name?: string
  asset_type?: string
  sheet_name?: string
  control_point?: string
  item_text?: string
  compliance_result?: string
  keyword?: string
}

export interface HistorySimilarQuery {
  ocr_text?: string
  asset_type?: string
  page_type?: string
  control_point?: string
  item_text?: string
}

export async function importHistoryExcel(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return unwrapResponse<HistoryImportResult>(
    apiClient.post('/history-records/import-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  )
}

export async function listHistoryRecords(filters?: HistoryRecordFilters) {
  return unwrapResponse<HistoryRecord[]>(apiClient.get('/history-records', { params: filters }))
}

export async function getHistoryRecord(recordId: string) {
  return unwrapResponse<HistoryRecord>(apiClient.get(`/history-records/${recordId}`))
}

export async function searchHistoryRecords(keyword: string) {
  return unwrapResponse<HistoryRecord[]>(apiClient.get('/history-records', { params: { keyword } }))
}

export async function getHistoryStats() {
  return unwrapResponse<HistoryStats>(apiClient.get('/history/stats'))
}

export async function getHistorySimilarRecords(query: HistorySimilarQuery) {
  return unwrapResponse<HistorySimilarRecord[]>(apiClient.post('/history-records/search-similar', query))
}

export async function getHistoryPhrases() {
  return unwrapResponse<HistoryPhraseSummary[]>(apiClient.get('/history/phrases'))
}
