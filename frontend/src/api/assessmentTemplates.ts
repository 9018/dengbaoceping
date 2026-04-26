import apiClient, { unwrapResponse } from './http'
import type {
  AssessmentTemplateImportResult,
  AssessmentTemplateItem,
  AssessmentTemplateSheet,
  AssessmentTemplateWorkbook,
  AssessmentTemplateWorkbookDetail,
  TemplateGuidebookLink,
  TemplateGuidebookLinkResult,
  TemplateHistoryLink,
  TemplateHistoryLinkResult,
} from '@/types/domain'

export interface AssessmentTemplateItemFilters {
  workbook_id?: string
  sheet_name?: string
  object_type?: string
  object_category?: string
  control_point?: string
  item_code?: string
  keyword?: string
  page_type?: string
}

export async function importAssessmentTemplateExcel(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return unwrapResponse<AssessmentTemplateImportResult>(
    apiClient.post('/assessment-templates/import-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  )
}

export async function listAssessmentTemplateWorkbooks() {
  return unwrapResponse<AssessmentTemplateWorkbook[]>(apiClient.get('/assessment-templates'))
}

export async function getAssessmentTemplateWorkbook(workbookId: string) {
  return unwrapResponse<AssessmentTemplateWorkbookDetail>(apiClient.get(`/assessment-templates/${workbookId}`))
}

export async function listAssessmentTemplateSheets(workbookId: string) {
  return unwrapResponse<AssessmentTemplateSheet[]>(apiClient.get(`/assessment-templates/${workbookId}/sheets`))
}

export async function listAssessmentTemplateItems(filters?: AssessmentTemplateItemFilters) {
  return unwrapResponse<AssessmentTemplateItem[]>(apiClient.get('/assessment-templates/items', { params: filters }))
}

export async function linkTemplateItemGuidebook(itemId: string) {
  return unwrapResponse<TemplateGuidebookLinkResult>(apiClient.post(`/assessment-template-items/${itemId}/link-guidebook`))
}

export async function listTemplateItemGuidebookLinks(itemId: string) {
  return unwrapResponse<TemplateGuidebookLink[]>(apiClient.get(`/assessment-template-items/${itemId}/guidebook-links`))
}

export async function linkTemplateItemHistory(itemId: string) {
  return unwrapResponse<TemplateHistoryLinkResult>(apiClient.post(`/assessment-template-items/${itemId}/link-history`))
}

export async function listTemplateItemHistoryLinks(itemId: string, compliance_result?: string) {
  return unwrapResponse<TemplateHistoryLink[]>(
    apiClient.get(`/assessment-template-items/${itemId}/history-links`, { params: compliance_result ? { compliance_result } : undefined }),
  )
}
