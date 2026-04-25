import apiClient, { unwrapResponse } from './http'
import type { Evidence, EvidenceHistoryMatchResult, EvidencePageClassification, EvidenceUploadPayload, ExtractedField, OcrResult } from '@/types/domain'

function buildEvidenceFormData(payload: EvidenceUploadPayload) {
  const formData = new FormData()
  formData.append('file', payload.file)
  if (payload.title) formData.append('title', payload.title)
  if (payload.evidence_type) formData.append('evidence_type', payload.evidence_type)
  if (payload.summary) formData.append('summary', payload.summary)
  if (payload.text_content) formData.append('text_content', payload.text_content)
  if (payload.device) formData.append('device', payload.device)
  if (payload.ports_json !== undefined) formData.append('ports_json', JSON.stringify(payload.ports_json))
  if (payload.evidence_time) formData.append('evidence_time', payload.evidence_time)
  if (payload.tags_json !== undefined) formData.append('tags_json', JSON.stringify(payload.tags_json))
  if (payload.source_ref) formData.append('source_ref', payload.source_ref)
  if (payload.category) formData.append('category', payload.category)
  if (payload.category_label) formData.append('category_label', payload.category_label)
  return formData
}

export async function listEvidences(projectId: string) {
  return unwrapResponse<Evidence[]>(apiClient.get(`/projects/${projectId}/evidences`))
}

export async function getEvidence(evidenceId: string) {
  return unwrapResponse<Evidence>(apiClient.get(`/evidences/${evidenceId}`))
}

export async function uploadEvidence(projectId: string, payload: EvidenceUploadPayload) {
  return unwrapResponse<Evidence>(
    apiClient.post(`/projects/${projectId}/evidences/upload`, buildEvidenceFormData(payload), {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  )
}

export async function runOcr(evidenceId: string, sampleId?: string, force = false) {
  return unwrapResponse<Evidence>(apiClient.post(`/evidences/${evidenceId}/ocr`, { sample_id: sampleId || null, force }))
}

export async function getOcrResult(evidenceId: string) {
  return unwrapResponse<OcrResult>(apiClient.get(`/evidences/${evidenceId}/ocr-result`))
}

export async function extractFields(evidenceId: string, templateCode?: string, force = false) {
  return unwrapResponse<ExtractedField[]>(
    apiClient.post(`/evidences/${evidenceId}/extract-fields`, { template_code: templateCode || null, force }),
  )
}

export async function listEvidenceFields(evidenceId: string) {
  return unwrapResponse<ExtractedField[]>(apiClient.get(`/evidences/${evidenceId}/fields`))
}

export async function matchEvidenceAsset(evidenceId: string, force = false) {
  return unwrapResponse<Evidence>(apiClient.post(`/evidences/${evidenceId}/match-asset`, { force }))
}

export async function confirmEvidenceAsset(evidenceId: string, assetId?: string | null) {
  return unwrapResponse<Evidence>(apiClient.post(`/evidences/${evidenceId}/confirm-asset`, { asset_id: assetId || null }))
}

export async function matchEvidenceGuidance(evidenceId: string, force = false) {
  return unwrapResponse<Evidence>(apiClient.post(`/evidences/${evidenceId}/match-guidance`, { force }))
}

export async function confirmEvidenceGuidance(evidenceId: string, guidanceId?: string | null) {
  return unwrapResponse<Evidence>(apiClient.post(`/evidences/${evidenceId}/confirm-guidance`, { guidance_id: guidanceId || null }))
}

export async function matchEvidenceHistory(evidenceId: string, payload: Record<string, unknown> = {}) {
  return unwrapResponse<EvidenceHistoryMatchResult>(apiClient.post(`/evidences/${evidenceId}/match-history`, payload))
}

export async function classifyEvidencePage(evidenceId: string, payload: Record<string, unknown> = {}) {
  return unwrapResponse<EvidencePageClassification>(apiClient.post(`/evidences/${evidenceId}/classify-page`, payload))
}

export async function deleteEvidence(evidenceId: string) {
  return unwrapResponse<null>(apiClient.delete(`/evidences/${evidenceId}`))
}
