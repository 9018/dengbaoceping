import apiClient, { unwrapResponse } from './http'
import type { AuditLog, EvaluationRecord, RecordGeneratePayload, RecordReviewPayload, RecordUpdatePayload } from '@/types/domain'

export async function listRecords(projectId: string) {
  return unwrapResponse<EvaluationRecord[]>(apiClient.get(`/projects/${projectId}/records`))
}

export async function getRecord(recordId: string) {
  return unwrapResponse<EvaluationRecord>(apiClient.get(`/records/${recordId}`))
}

export async function generateRecord(projectId: string, payload: RecordGeneratePayload) {
  return unwrapResponse<EvaluationRecord>(apiClient.post(`/projects/${projectId}/records/generate`, payload))
}

export async function updateRecord(recordId: string, payload: RecordUpdatePayload) {
  return unwrapResponse<EvaluationRecord>(apiClient.put(`/records/${recordId}`, payload))
}

export async function reviewRecord(recordId: string, payload: RecordReviewPayload) {
  return unwrapResponse<EvaluationRecord>(apiClient.post(`/records/${recordId}/review`, payload))
}

export async function listRecordAuditLogs(recordId: string) {
  return unwrapResponse<AuditLog[]>(apiClient.get(`/records/${recordId}/audit-logs`))
}
