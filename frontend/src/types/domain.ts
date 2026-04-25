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
  asset_kind: string
  category: string
  category_label: string
  batch_no: string | null
  filename: string
  primary_ip: string | null
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
  asset_kind?: string
  category: string
  category_label: string
  batch_no?: string | null
  filename: string
  primary_ip?: string | null
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

export interface AssetMatchReasons {
  summary?: string[]
  matched_asset_id?: string | null
  asset_name?: string | null
  asset_type?: string | null
  score?: number | null
  score_breakdown?: Record<string, number>
  signals?: Record<string, unknown>
  need_create_asset?: boolean
  suggested_asset_name?: string | null
  suggested_asset_type?: string | null
  confirmed_asset_id?: string | null
  confirmed_asset_name?: string | null
  confirmed_asset_type?: string | null
}

export interface GuidanceEvidenceHistory {
  history_record_id: string
  sheet_name: string
  asset_name: string | null
  asset_type: string | null
  compliance_status: string | null
  match_score: number
  match_reason: GuidanceMatchReason | Record<string, unknown>
}

export interface GuidanceMatchReasons {
  summary?: string[]
  matched_guidance_id?: string | null
  guidance_code?: string | null
  section_title?: string | null
  section_path?: string | null
  score?: number | null
  score_breakdown?: Record<string, unknown>
  signals?: Record<string, unknown>
  history_count?: number
  top_history?: GuidanceEvidenceHistory[]
  confirmed_guidance_id?: string | null
  confirmed_guidance_code?: string | null
  confirmed_section_title?: string | null
}

export interface Evidence extends Timestamped {
  id: string
  project_id: string
  asset_id: string | null
  matched_asset_id: string | null
  matched_guidance_id: string | null
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
  asset_match_score: number | null
  asset_match_reasons_json: AssetMatchReasons | Record<string, unknown> | null
  asset_match_status: string | null
  guidance_match_score: number | null
  guidance_match_reasons_json: GuidanceMatchReasons | Record<string, unknown> | null
  guidance_match_status: string | null
  matched_asset?: Asset | null
  matched_guidance?: GuidanceItem | null
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

export interface MatchFieldSnapshot {
  field_code: string
  field_name: string
  value: string | null
  status: string | null
}

export interface MatchReasons {
  summary?: string[]
  matched_required_fields?: string[]
  missing_required_fields?: string[]
  matched_optional_fields?: string[]
  missing_optional_fields?: string[]
  matched_negative_fields?: string[]
  clean_negative_fields?: string[]
  matched_template_fields?: string[]
  missing_template_fields?: string[]
  device_type?: string | null
  device_type_reason?: string
  required_fields_score?: number
  optional_fields_score?: number
  negative_fields_score?: number
  template_coverage?: number
  device_type_score?: number
  pass_score?: number
  domain?: string | null
  level2?: string | null
  level3?: string | null
  selected?: MatchReasons
  best_match_item_code?: string | null
  selection_mode?: string
}

export interface MatchCandidate {
  item_code: string | null
  template_code: string | null
  score: number | null
  pass_score: number | null
  missing_fields: string[]
  matched_fields: MatchFieldSnapshot[]
  reasons: MatchReasons
}

export interface EvaluationRecord extends Timestamped {
  id: string
  project_id: string
  asset_id: string | null
  evidence_ids: string[]
  title: string | null
  record_content: string | null
  final_content: string | null
  matched_fields_json: MatchFieldSnapshot[] | Record<string, unknown> | null
  match_candidates: MatchCandidate[] | Record<string, unknown> | null
  status: string
  review_comment: string | null
  reviewed_by: string | null
  reviewed_at: string | null
  match_score: number | null
  match_reasons: MatchReasons | Record<string, unknown> | null
  template_code: string | null
  item_code: string | null
}

export interface RecordGeneratePayload {
  evidence_id: string
  device_type_override?: string | null
  selected_item_code?: string | null
  selected_template_code?: string | null
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

export interface HistoryRecord extends Timestamped {
  id: string
  source_file: string
  sheet_name: string
  asset_name: string
  asset_type: string | null
  extension_standard: string | null
  control_point: string | null
  evaluation_item: string | null
  record_text: string | null
  compliance_status: string | null
  score: number | null
  item_no: string | null
  row_index: number
  keywords_json: string[]
}

export interface HistoryImportResult {
  source_file: string
  sheet_count: number
  imported_count: number
  skipped_count: number
  compliance_status_counts: Record<string, number>
}

export interface HistoryStats {
  sheet_count: number
  total: number
  compliance_status_counts: Record<string, number>
  asset_type_counts: Record<string, number>
}

export interface HistorySimilarRecord {
  id: string
  sheet_name: string
  asset_name: string
  asset_type: string | null
  control_point: string | null
  evaluation_item: string | null
  compliance_status: string | null
  score: number
  reasons: string[]
}

export interface HistoryPhraseSummary {
  phrase: string
  total: number
  compliance_status_counts: Record<string, number>
}

export interface GuidanceMatchReason {
  summary: string[]
  guidance_asset_type: string | null
  history_asset_type: string | null
  keyword_overlap: string[]
  control_point_hits: string[]
  evaluation_text_hits: string[]
}

export interface GuidanceHistoryMatch {
  guidance_item_id: string
  history_record_id: string
  match_score: number
  match_reason: GuidanceMatchReason
  record_text: string | null
  compliance_status: string | null
  asset_type: string | null
  control_point: string | null
  evaluation_item: string | null
  sheet_name: string
}

export interface HistoryGuidanceMatch {
  history_record_id: string
  guidance_item_id: string
  match_score: number
  match_reason: GuidanceMatchReason
  section_title: string
  section_path: string
  guidance_code: string
}

export interface GuidanceHistoryLinkResult {
  guidance_item_id: string
  linked_count: number
  updated_count: number
  top_score: number | null
}

export interface GuidanceItem extends Timestamped {
  id: string
  guidance_code: string
  source_file: string
  section_path: string
  section_title: string
  level1: string | null
  level2: string | null
  level3: string | null
  raw_markdown: string
  plain_text: string
  keywords_json: string[]
  check_points_json: string[]
  evidence_requirements_json: string[]
  record_suggestion: string | null
}

export interface GuidanceLibrary {
  source_file: string
  absolute_path: string
  file_exists: boolean
  file_empty: boolean
  file_message: string
  imported: boolean
  total: number
  keyword: string | null
  items: GuidanceItem[]
}

export interface GuidanceImportResult {
  source_file: string
  absolute_path: string
  file_exists: boolean
  file_empty: boolean
  file_message: string
  imported: boolean
  total: number
  imported_count: number
}

export type GuidanceSearchResult = GuidanceItem[]

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
  mode: string | null
  status: string
  file_name: string
  file_size: number
  record_count: number
}

export interface ExportCreatePayload {
  format?: string
}

export interface ExcelExportCreatePayload {
  mode: 'official' | 'debug'
}

export interface ProjectSummary {
  assetCount: number
  evidenceCount: number
  recordCount: number
  pendingReviewCount: number
}

export interface TemplateGenerationDefinition {
  title_template: string
  record_template: string
  fallbacks: Record<string, string>
  default_review_comment: string
}

export interface TemplateDefinition {
  template_code: string
  name: string
  template_type: string
  extension_type: string
  domain: string
  description: string
  field_codes: string[]
  generation: TemplateGenerationDefinition
}

export interface FieldRuleDefinition {
  field_code: string
  field_group: string
  field_name: string
  value_type: string
  aliases: string[]
  regex: string[]
  required: boolean
  status_when_missing: string
}

export interface EvaluationItemDefinition {
  item_code: string
  template_code: string
  domain: string
  level2: string
  level3: string
  required_fields: string[]
  device_types: string[]
  pass_score: number
}
