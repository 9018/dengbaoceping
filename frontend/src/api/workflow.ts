import apiClient, { unwrapResponse } from './http'
import type {
  EvidenceFactExtractionResult,
  PageResult,
  ProjectAssessmentConfirmPayload,
  ProjectAssessmentDraftResult,
  ProjectAssessmentItem,
  ProjectAssessmentItemMatchResult,
  ProjectAssessmentTable,
  WorkflowGlobalStatus,
  WorkflowNextAction,
  WorkflowProjectStatus,
} from '@/types/domain'

export async function getWorkflowGlobalStatus() {
  return unwrapResponse<WorkflowGlobalStatus>(apiClient.get('/workflow/global-status'))
}

export async function importWorkflowTemplate(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return unwrapResponse<Record<string, unknown>>(
    apiClient.post('/workflow/import-template', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  )
}

export async function importWorkflowGuidance() {
  return unwrapResponse<Record<string, unknown>>(apiClient.post('/workflow/import-guidance'))
}

export async function importWorkflowHistory(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return unwrapResponse<Record<string, unknown>>(
    apiClient.post('/workflow/import-history', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  )
}

export async function getProjectWorkflowStatus(projectId: string) {
  return unwrapResponse<WorkflowProjectStatus>(apiClient.get(`/projects/${projectId}/workflow/status`))
}

export async function getProjectAssessmentNextAction(projectId: string) {
  return unwrapResponse<WorkflowNextAction>(apiClient.get(`/projects/${projectId}/assessment-next-action`))
}

export async function generateProjectAssessmentTable(projectId: string, assetId: string, force = false) {
  return unwrapResponse<ProjectAssessmentTable>(
    apiClient.post(`/projects/${projectId}/assets/${assetId}/generate-assessment-table`, null, { params: { force } }),
  )
}

export async function listProjectAssessmentTables(projectId: string, page = 1, pageSize = 20) {
  return unwrapResponse<PageResult<ProjectAssessmentTable>>(
    apiClient.get(`/projects/${projectId}/assessment-tables`, { params: { page, page_size: pageSize } }),
  )
}

export async function listProjectAssessmentItems(tableId: string, page = 1, pageSize = 50) {
  return unwrapResponse<PageResult<ProjectAssessmentItem>>(
    apiClient.get(`/assessment-tables/${tableId}/items`, { params: { page, page_size: pageSize } }),
  )
}

export async function extractEvidenceFacts(evidenceId: string) {
  return unwrapResponse<EvidenceFactExtractionResult>(apiClient.post(`/evidences/${evidenceId}/extract-facts`))
}

export async function matchProjectAssessmentItem(evidenceId: string, projectId: string, assetId?: string) {
  return unwrapResponse<ProjectAssessmentItemMatchResult>(
    apiClient.post(`/evidences/${evidenceId}/match-project-assessment-item`, null, {
      params: assetId ? { project_id: projectId, asset_id: assetId } : { project_id: projectId },
    }),
  )
}

export async function generateProjectAssessmentDraft(itemId: string, evidenceId: string) {
  return unwrapResponse<ProjectAssessmentDraftResult>(
    apiClient.post(`/project-assessment-items/${itemId}/generate-draft`, null, { params: { evidence_id: evidenceId } }),
  )
}

export async function confirmProjectAssessmentItem(itemId: string, payload: ProjectAssessmentConfirmPayload) {
  return unwrapResponse<ProjectAssessmentItem>(
    apiClient.post(`/project-assessment-items/${itemId}/confirm`, null, { params: payload }),
  )
}
