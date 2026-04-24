import apiClient, { unwrapResponse } from './http'
import type { AuditLog, ExtractedField, FieldReviewPayload, FieldUpdatePayload } from '@/types/domain'

export async function updateField(fieldId: string, payload: FieldUpdatePayload) {
  return unwrapResponse<ExtractedField>(apiClient.put(`/fields/${fieldId}`, payload))
}

export async function reviewField(fieldId: string, payload: FieldReviewPayload) {
  return unwrapResponse<ExtractedField>(apiClient.post(`/fields/${fieldId}/review`, payload))
}

export async function listFieldAuditLogs(fieldId: string) {
  return unwrapResponse<AuditLog[]>(apiClient.get(`/fields/${fieldId}/audit-logs`))
}
