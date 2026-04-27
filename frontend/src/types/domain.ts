export interface ApiError {
  code: string
  message: string
  details?: unknown
}

export interface ApiMeta {
  total: number
  page?: number
  page_size?: number
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
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
  ocr_error_message: string | null
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

export type EvidencePageType =
  | 'password_policy'
  | 'login_failure_lock'
  | 'session_timeout'
  | 'remote_management_protocol'
  | 'admin_account'
  | 'user_role_permission'
  | 'access_control_policy'
  | 'security_policy'
  | 'intrusion_prevention'
  | 'antivirus'
  | 'audit_log'
  | 'system_log'
  | 'log_server_config'
  | 'signature_update'
  | 'system_version'
  | 'ha_status'

export interface EvidencePageClassification {
  page_type: EvidencePageType | null
  confidence: number
  reason: string
  matched_keywords: string[]
}

export interface EvidenceHistoryMatchedRecord {
  id: string
  sheet_name: string
  asset_name: string
  asset_type: string | null
  control_point: string | null
  item_text: string | null
  evaluation_item: string | null
  record_text: string | null
  raw_text: string | null
  compliance_result: string | null
  compliance_status: string | null
  score: number
  reasons: string[]
}

export interface EvidenceHistoryMatchResult {
  matched_history_records: EvidenceHistoryMatchedRecord[]
  suggested_control_point: string | null
  suggested_item_text: string | null
  suggested_record_text: string | null
  suggested_compliance_result: string | null
  confidence: number
  reason: string
  page_type: EvidencePageType | null
  page_confidence: number
}

export interface EvidenceTemplateItemCandidate {
  id: string
  sheet_name: string
  row_index: number
  item_code: string | null
  object_type: string | null
  object_category: string | null
  control_point: string | null
  item_text: string | null
  record_template: string | null
  default_compliance_result: string | null
  page_types_json: string[]
  score: number
  reasons: string[]
  matched_keywords: string[]
}

export interface EvidenceTemplateItemMatchResult {
  matched_template_item: EvidenceTemplateItemCandidate | null
  candidates: EvidenceTemplateItemCandidate[]
  score: number
  confidence: number
  reason: string[]
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
  raw_status?: string
  sample_id?: string
  full_text?: string
  lines?: Array<{ text: string; confidence?: number | null; bbox?: unknown[] }>
  pages?: unknown
  evidence_id?: string
  filename?: string
  file_path?: string
  processed_at?: string
  error?: { code?: string; message?: string; details?: unknown } | null
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

export interface RecordTemplateSnapshot {
  template_id?: string | null
  template_name?: string | null
  template_type?: string | null
  sheet_name?: string | null
  row_no?: number | null
  item_no?: string | null
  extension_standard?: string | null
  control_point?: string | null
  evaluation_item?: string | null
  record_template?: string | null
  default_compliance?: string | null
  score_weight?: number | null
}

export interface RecordGenerationDetails {
  compliance_result?: string | null
  confidence?: number | null
  evidence_summary?: string[]
  missing_evidence?: string[]
  page_type?: string | null
  history_record_ids?: string[]
  template_snapshot?: RecordTemplateSnapshot | null
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
  match_source?: string | null
  selected?: MatchReasons
  best_match_item_code?: string | null
  selection_mode?: string
  record_generation?: RecordGenerationDetails
}

export interface MatchCandidate {
  match_source?: string | null
  item_code: string | null
  item_no?: string | null
  template_code: string | null
  template_id?: string | null
  evaluation_item_id?: string | null
  sheet_name?: string | null
  record_no?: string | null
  source_row_no?: number | null
  score: number | null
  pass_score: number | null
  missing_fields: string[]
  matched_fields: MatchFieldSnapshot[]
  reasons: MatchReasons
}

export interface EvaluationRecord extends Timestamped {
  id: string
  project_id: string
  template_id?: string | null
  evaluation_item_id?: string | null
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
  record_no?: string | null
  sheet_name?: string | null
  source_row_no?: number | null
  template_snapshot_json?: RecordTemplateSnapshot | Record<string, unknown> | null
  conclusion: string | null
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
  project_name: string | null
  sheet_name: string
  asset_name: string
  asset_type: string | null
  asset_ip: string | null
  asset_version: string | null
  standard_type: string | null
  extension_standard: string | null
  control_point: string | null
  item_text: string | null
  evaluation_item: string | null
  record_text: string | null
  raw_text: string | null
  compliance_result: string | null
  compliance_status: string | null
  score_weight: number | null
  score: number | null
  item_code: string | null
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
  source_file: string | null
  project_name: string | null
  sheet_name: string
  asset_name: string
  asset_type: string | null
  asset_ip: string | null
  asset_version: string | null
  standard_type: string | null
  control_point: string | null
  item_text: string | null
  evaluation_item: string | null
  record_text: string | null
  raw_text: string | null
  compliance_result: string | null
  compliance_status: string | null
  score_weight: number | null
  item_code: string | null
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

export interface TemplateGuidebookLinkResult {
  template_item_id: string
  linked_count: number
  updated_count: number
  top_score: number | null
}

export interface TemplateHistoryLinkResult {
  template_item_id: string
  linked_count: number
  updated_count: number
  top_score: number | null
}

export interface TemplateHistoryLink {
  template_item_id: string
  history_record_id: string
  match_score: number
  match_reason: {
    summary: string[]
    template_item_id?: string
    history_record_id?: string
    template_object_type?: string | null
    template_object_category?: string | null
    history_asset_type?: string | null
    control_point_hits?: string[]
    item_text_hits?: string[]
    record_similarity?: number | null
    template_compliance_result?: string | null
    history_compliance_result?: string | null
  }
  history_record: HistoryRecord
  sheet_name: string
  asset_name: string
  asset_type: string | null
  control_point: string | null
  item_text: string | null
  evaluation_item: string | null
  record_text: string | null
  raw_text: string | null
  compliance_result: string | null
  compliance_status: string | null
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

export interface TemplateGuidebookLink {
  template_item_id: string
  guidance_item_id: string
  match_score: number
  match_reason: {
    summary: string[]
    template_item_id?: string
    guidance_item_id?: string
    template_object_type?: string | null
    template_object_category?: string | null
    guidance_asset_type?: string | null
    control_point_hits?: string[]
    item_text_hits?: string[]
    evidence_hits?: string[]
    item_no_match?: string | null
  }
  guidance_item: GuidanceItem
  section_title: string
  section_path: string
  guidance_code: string
  check_points: string[]
  evidence_requirements: string[]
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

export interface ProjectTemplateSummary extends Timestamped {
  template_id: string
  project_id: string
  name: string
  template_type: string
  version: string | null
  source_asset_id: string | null
  source_file: string | null
  sheet_count: number
  sheet_names: string[]
  item_count: number
  is_active: boolean
}

export interface AssessmentTemplateImportResult {
  workbook_id: string
  source_file: string
  name: string
  version: string | null
  sheet_count: number
  sheet_names: string[]
  item_count: number
  imported_count: number
  skipped_count: number
}

export interface AssessmentTemplateWorkbook extends Timestamped {
  id: string
  source_file: string
  name: string
  version: string | null
  sheet_count: number
  item_count: number
}

export interface AssessmentTemplateWorkbookDetail extends AssessmentTemplateWorkbook {
  object_type_counts: Record<string, number>
  object_category_counts: Record<string, number>
  control_point_counts: Record<string, number>
}

export interface AssessmentTemplateSheet extends Timestamped {
  id: string
  workbook_id: string
  sheet_name: string
  object_type: string | null
  object_category: string | null
  object_subtype: string | null
  is_physical: boolean
  is_network: boolean
  is_security_device: boolean
  is_server: boolean
  is_database: boolean
  is_middleware: boolean
  is_application: boolean
  is_data_object: boolean
  is_management: boolean
  row_count: number
}

export interface AssessmentTemplateItem extends Timestamped {
  id: string
  workbook_id: string
  sheet_id: string
  sheet_name: string
  row_index: number
  standard_type: string | null
  control_point: string | null
  item_text: string | null
  record_template: string | null
  default_compliance_result: string | null
  weight: number | null
  item_code: string | null
  object_type: string | null
  object_category: string | null
  page_types_json: string[] | Record<string, unknown> | null
  required_facts_json: string[] | Record<string, unknown> | null
  evidence_keywords_json: string[] | Record<string, unknown> | null
  command_keywords_json: string[] | Record<string, unknown> | null
  applicability_json: string[] | Record<string, unknown> | null
  raw_row_json: Record<string, unknown> | unknown[] | null
}

export interface WorkflowGlobalStatus {
  template_workbook_count: number
  template_item_count: number
  guidance_item_count: number
  history_record_count: number
  canNext: boolean
  status: string
  summary: string
}

export type WorkflowStage =
  | 'global_template_missing'
  | 'guidance_missing'
  | 'history_missing'
  | 'asset_missing'
  | 'table_missing'
  | 'evidence_missing'
  | 'ocr_pending'
  | 'facts_missing'
  | 'item_match_missing'
  | 'draft_missing'
  | 'confirm_missing'
  | 'next_item'
  | 'completed'

export type WorkflowStepKey = 'setup' | 'asset' | 'table' | 'evidence' | 'ocr' | 'facts' | 'match' | 'draft' | 'confirm' | 'export'

export interface WorkflowProjectStats {
  asset_count: number
  table_count: number
  item_count: number
  evidence_count: number
  ocr_completed_count: number
  fact_count: number
  matched_item_count: number
  drafted_item_count: number
  confirmed_item_count: number
  pending_item_count: number
  pending_review_count: number
}

export interface WorkflowNextAction {
  project_id: string
  stage: WorkflowStage
  step_key: WorkflowStepKey
  step_index: number
  route: string
  message: string
  table_id: string | null
  item_id: string | null
  asset_id: string | null
  evidence_id: string | null
  stats: WorkflowProjectStats
}

export interface WorkflowProjectStatus {
  project_id: string
  table_count: number
  item_count: number
  status: WorkflowStage
  canNext: boolean
  summary: string
  next_action: WorkflowNextAction
  stats: WorkflowProjectStats
}

export interface ProjectAssessmentTable extends Timestamped {
  id: string
  project_id: string
  asset_id: string
  source_workbook_id: string | null
  name: string
  status: string
  item_count: number
}

export interface EvidenceFact extends Timestamped {
  id: string
  project_id: string
  asset_id: string | null
  evidence_id: string
  project_assessment_item_id: string | null
  matched_template_item_id: string | null
  page_type: string | null
  fact_group: string
  fact_key: string
  fact_name: string
  raw_value: string | null
  normalized_value: string | null
  value_number: number | null
  value_bool: boolean | null
  value_json: Record<string, unknown> | unknown[] | null
  source_text: string | null
  source_page: number | null
  confidence: number | null
  status: string
}

export interface EvidenceFactExtractionResult {
  page_type: string
  confidence: number
  reason: string
  matched_keywords: string[]
  facts: EvidenceFact[]
}

export interface ProjectAssessmentItem extends Timestamped {
  id: string
  table_id: string
  project_id: string
  asset_id: string
  source_template_item_id: string | null
  sheet_name: string
  row_index: number
  standard_type: string | null
  control_point: string | null
  item_text: string | null
  record_template: string | null
  default_compliance_result: string | null
  weight: number | null
  item_code: string | null
  object_type: string | null
  object_category: string | null
  page_types_json: string[] | Record<string, unknown> | null
  required_facts_json: string[] | Record<string, unknown> | null
  evidence_keywords_json: string[] | Record<string, unknown> | null
  command_keywords_json: string[] | Record<string, unknown> | null
  applicability_json: string[] | Record<string, unknown> | null
  evidence_ids_json: string[] | Record<string, unknown> | null
  evidence_facts_json: Array<Record<string, unknown>> | Record<string, unknown> | null
  guidance_refs_json: Array<Record<string, unknown>> | Record<string, unknown> | null
  history_refs_json: Array<Record<string, unknown>> | Record<string, unknown> | null
  draft_record_text: string | null
  draft_compliance_result: string | null
  final_record_text: string | null
  final_compliance_result: string | null
  confidence: number | null
  match_score: number | null
  match_reason_json: Record<string, unknown> | unknown[] | null
  status: string
  review_comment: string | null
  reviewed_by: string | null
  reviewed_at: string | null
}

export interface ProjectAssessmentItemMatchCandidate {
  project_assessment_item_id: string
  table_id: string
  sheet_name: string
  row_index: number
  item_code: string | null
  control_point: string | null
  item_text: string | null
  score: number
  reasons: string[]
  matched_keywords: string[]
}

export interface ProjectAssessmentItemMatchResult {
  matched_project_assessment_item: ProjectAssessmentItemMatchCandidate | null
  candidates: ProjectAssessmentItemMatchCandidate[]
  score: number
  confidence: number
  reason: string[]
}

export interface ProjectAssessmentDraftResult {
  project_assessment_item_id: string
  draft_record_text: string | null
  draft_compliance_result: string | null
  confidence: number | null
  reason: string[]
  missing_evidence: string[]
  guidance_refs: Array<Record<string, unknown>>
  history_refs: Array<Record<string, unknown>>
  evidence_facts: Array<Record<string, unknown>>
}

export interface ProjectAssessmentConfirmPayload {
  final_record_text?: string | null
  final_compliance_result?: string | null
  review_comment?: string | null
  reviewed_by?: string | null
}

export interface TemplateGenerationDefinition {
  title_template: string
  record_template: string
  fallbacks: Record<string, string>
  default_review_comment: string
}
