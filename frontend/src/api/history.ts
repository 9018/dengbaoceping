import apiClient, { unwrapResponse } from './http'
import type {
  HistoryDuplicateGroup,
  HistoryFieldValue,
  HistoryFieldValueRenamePayload,
  HistoryImportResult,
  HistoryPhraseSummary,
  HistoryRecord,
  HistorySimilarRecord,
  HistoryStats,
  HistorySummary,
  PageResult,
} from '@/types/domain'

export interface HistoryRecordFilters {
  asset_name?: string
  asset_type?: string
  sheet_name?: string
  control_point?: string
  item_text?: string
  compliance_result?: string
  keyword?: string
  page?: number
  page_size?: number
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
  return unwrapResponse<PageResult<HistoryRecord>>(apiClient.get('/history-records', { params: filters }))
}

export async function getHistoryRecord(recordId: string) {
  return unwrapResponse<HistoryRecord>(apiClient.get(`/history-records/${recordId}`))
}

export async function searchHistoryRecords(keyword: string) {
  return unwrapResponse<PageResult<HistoryRecord>>(apiClient.get('/history-records', { params: { keyword } }))
}

export async function getHistoryStats() {
  return unwrapResponse<HistoryStats>(apiClient.get('/history/stats'))
}

export async function getHistorySummary() {
  return unwrapResponse<HistorySummary>(apiClient.get('/history-records/summary'))
}

export async function getHistoryDuplicateGroups(filters?: HistoryRecordFilters) {
  return unwrapResponse<HistoryDuplicateGroup[]>(apiClient.get('/history-records/duplicates', { params: filters }))
}

export async function deleteHistoryDuplicateGroups(strategy = 'keep_first', force = false) {
  return unwrapResponse<{ strategy: string; duplicate_group_count: number; deleted_count: number; linked_template_count: number; linked_guidance_count: number; forced: boolean }>(
    apiClient.delete('/history-records/duplicates', { params: { strategy, force } }),
  )
}

export async function listHistoryFieldValues(fieldName: string) {
  return unwrapResponse<HistoryFieldValue[]>(apiClient.get(`/history-records/field-values/${fieldName}`))
}

export async function renameHistoryFieldValue(fieldName: string, payload: HistoryFieldValueRenamePayload) {
  return unwrapResponse<{ field_name: string; from_value: string; to_value: string; updated_count: number }>(
    apiClient.patch(`/history-records/field-values/${fieldName}`, payload),
  )
}

export async function deleteHistoryRecordsByFieldValue(fieldName: string, value: string, force = false) {
  return unwrapResponse<{ field_name: string; field_value: string; deleted_count: number; linked_template_count: number; linked_guidance_count: number; forced: boolean }>(
    apiClient.delete(`/history-records/field-values/${fieldName}`, { params: { value, force } }),
  )
}

export async function getHistorySimilarRecords(query: HistorySimilarQuery) {
  return unwrapResponse<HistorySimilarRecord[]>(apiClient.post('/history-records/search-similar', query))
}

export async function getHistoryPhrases() {
  return unwrapResponse<HistoryPhraseSummary[]>(apiClient.get('/history/phrases'))
}
