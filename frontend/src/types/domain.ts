export interface ApiError {
  code: string
  message: string
  details?: unknown
}

export interface ApiMeta {
  total: number
}

export interface ApiResponse<T> {
  success: boolean
  message?: string
  data: T
  meta?: ApiMeta
  error?: ApiError
}

export interface Timestamped {
  created_at: string
  updated_at: string
}

export interface Project extends Timestamped {
  id: string
  code: string | null
  name: string
  project_type: string
  status: string
  description: string | null
  storage_root: string | null
}

export interface ProjectPayload {
  code?: string | null
  name: string
  project_type?: string
  status?: string
  description?: string | null
  storage_root?: string | null
}

export interface Asset extends Timestamped {
  id: string
  project_id: string
  category: string
  category_label: string
  batch_no: string | null
  filename: string
  file_ext: string | null
  mime_type: string | null
  relative_path: string
  absolute_path: string | null
  file_size: number | null
  file_sha256: string | null
  file_mtime: string | null
  source: string | null
  ingest_status: string
}

export interface AssetPayload {
  category: string
  category_label: string
  batch_no?: string | null
  filename: string
  file_ext?: string | null
  mime_type?: string | null
  relative_path: string
  absolute_path?: string | null
  file_size?: number | null
  file_sha256?: string | null
  file_mtime?: string | null
  source?: string | null
  ingest_status?: string
}

export interface Evidence extends Timestamped {
  id: string
  project_id: string
  asset_id: string | null
  evidence_type: string
  title: string
  summary: string | null
  text_content: string | null
  ocr_result_json: unknown
  ocr_status: string | null
  ocr_provider: string | null
  ocr_processed_at: string | null
  device: string | null
  ports_json: unknown
  evidence_time: string | null
  tags_json: unknown
  source_ref: string | null
}

export interface EvidenceUploadPayload {
  file: File
  title?: string
  evidence_type?: string
  summary?: string
  text_content?: string
  device?: string
  ports_json?: unknown
  evidence_time?: string
  tags_json?: unknown
  source_ref?: string
  category?: string
  category_label?: string
}

export interface OcrResult {
  provider?: string
  status?: string
  sample_id?: string
  full_text?: string
  pages?: unknown
  evidence_id?: string
  filename?: string
  file_path?: string
  processed_at?: string
}

export interface ExtractedField extends Timestamped {
  id: string
  evidence_id: string | null
  field_group: string
  field_name: string
  raw_value: string | null
  corrected_value: string | null
  source_text: string | null
  confidence: number | null
  status: string | null
  review_comment: string | null
  reviewed_by: string | null
  reviewed_at: string | null
  source_page: number | null
  source_sheet: string | null
  source_row: number | null
  rule_id: string | null
}

export interface FieldUpdatePayload {
  raw_value?: string | null
  corrected_value?: string | null
  confidence?: number | null
  source_text?: string | null
  status?: string | null
  review_comment?: string | null
  reviewed_by?: string | null
}

export interface FieldReviewPayload {
  status: string
  corrected_value?: string | null
  review_comment?: string | null
  reviewed_by?: string | null
}

export interface EvaluationRecord extends Timestamped {
  id: string
  project_id: string
  asset_id: string | null
  evidence_ids: string[]
  title: string | null
  record_content: string | null
  final_content: string | null
  matched_fields_json: unknown
  status: string
  review_comment: string | null
  reviewed_by: string | null
  reviewed_at: string | null
  match_score: number | null
  match_reasons: unknown
  template_code: string | null
  item_code: string | null
}

export interface RecordGeneratePayload {
  evidence_id: string
  device_type_override?: string | null
  force_regenerate?: boolean
}

export interface RecordUpdatePayload {
  record_content?: string | null
  final_content?: string | null
  status?: string | null
  review_comment?: string | null
  reviewed_by?: string | null
}

export interface RecordReviewPayload {
  status: string
  final_content?: string | null
  review_comment?: string | null
  reviewed_by?: string | null
}

export interface AuditLog {
  id: string
  target_type: string
  target_id: string
  action: string
  changed_fields_json: unknown
  review_comment: string | null
  reviewed_by: string | null
  created_at: string
}

export interface ExportJob extends Timestamped {
  id: string
  project_id: string
  format: string
  status: string
  file_name: string
  file_size: number
  record_count: number
}

export interface ExportCreatePayload {
  format?: string
}

export interface ProjectSummary {
  assetCount: number
  evidenceCount: number
  recordCount: number
  pendingReviewCount: number
}
