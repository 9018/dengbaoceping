<template>
  <AppShell :project-id="projectId" title="识别复核页" subtitle="三栏联动展示证据概览、OCR 文本和字段修正结果，形成复核闭环。">
    <div class="page-stack">
      <el-card>
        <template #header>
          <div class="card-toolbar">
            <div class="section-header">
              <div class="section-title">证据选择</div>
              <div class="section-subtitle">切换证据后，左侧上下文、中间 OCR 文本和右侧字段修正表单会同步刷新。</div>
            </div>
            <el-space wrap>
              <el-select v-model="selectedEvidenceId" placeholder="请选择证据" style="width: 360px" @change="loadReviewData">
                <el-option v-for="item in evidences" :key="item.id" :label="`${item.title} (${item.device || '未绑定设备'})`" :value="item.id" />
              </el-select>
              <el-button @click="loadReviewData">刷新</el-button>
            </el-space>
          </div>
        </template>
      </el-card>

      <div class="review-grid">
        <el-card class="review-column">
          <template #header>
            <div class="section-header">
              <div class="section-title">证据文件预览</div>
              <div class="section-subtitle">当前后端未提供可直接嵌入浏览器的文件地址，因此左栏以元信息和流程状态为主。</div>
            </div>
          </template>
          <div class="preview-placeholder">
            <div class="preview-placeholder__icon">PREVIEW</div>
            <div class="preview-placeholder__title">暂无可用文件预览 URL</div>
            <div class="preview-placeholder__text">当前阶段先围绕证据上下文、OCR 文本与字段修正建立复核闭环。</div>
          </div>
          <div class="info-panel review-meta-panel">
            <div class="panel-label">证据上下文</div>
            <div class="meta-list">
              <span>证据标题：{{ currentEvidence?.title || '-' }}</span>
              <span>关联设备：{{ currentEvidence?.device || '未绑定设备' }}</span>
              <span>证据类型：{{ currentEvidence?.evidence_type || '-' }}</span>
              <span>来源标识：{{ currentEvidence?.source_ref || '未填写' }}</span>
            </div>
          </div>
          <el-descriptions :column="1" border class="meta-descriptions">
            <el-descriptions-item label="OCR 状态">
              <AppStatusTag kind="ocr" :status="currentEvidence?.ocr_status" />
            </el-descriptions-item>
            <el-descriptions-item label="OCR Provider">{{ currentEvidence?.ocr_provider || '-' }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ currentEvidence?.updated_at || '-' }}</el-descriptions-item>
            <el-descriptions-item label="当前匹配记录">
              {{ relatedRecord?.item_code || '尚未生成记录' }}
            </el-descriptions-item>
            <el-descriptions-item label="缺失字段提示">
              {{ relatedRecordMissingFields.length ? relatedRecordMissingFields.join('，') : '无' }}
            </el-descriptions-item>
          </el-descriptions>

          <el-card class="asset-match-card" shadow="never">
            <template #header>
              <div class="section-header">
                <div class="section-title">测试对象匹配</div>
                <div class="section-subtitle">基于 OCR 文本和抽取字段，建议当前证据对应的测试对象。</div>
              </div>
            </template>
            <el-space direction="vertical" fill>
              <div class="match-status-row">
                <AppStatusTag kind="asset" :status="assetMatchStatusTag" />
                <span class="muted-text">匹配分数：{{ currentEvidence?.asset_match_score ?? '-' }}</span>
              </div>
              <div class="meta-list compact">
                <span>建议资产：{{ currentEvidence?.matched_asset?.filename || matchReasons.asset_name || '未匹配' }}</span>
                <span>建议类型：{{ matchReasons.suggested_asset_type || currentEvidence?.matched_asset?.category || '未识别' }}</span>
                <span>建议名称：{{ matchReasons.suggested_asset_name || '未提取' }}</span>
              </div>
              <el-alert
                v-if="matchReasons.need_create_asset"
                type="warning"
                :closable="false"
                title="当前未匹配到现有测试对象，建议创建新资产后绑定。"
              />
              <div v-if="reasonList.length" class="reason-list">
                <div v-for="reason in reasonList" :key="reason" class="reason-item">- {{ reason }}</div>
              </div>
              <el-select v-model="selectedAssetId" clearable filterable placeholder="人工选择已有测试对象">
                <el-option
                  v-for="asset in testObjectAssets"
                  :key="asset.id"
                  :label="`${asset.filename}${asset.primary_ip ? ` (${asset.primary_ip})` : ''}`"
                  :value="asset.id"
                />
              </el-select>
              <el-space wrap>
                <el-button type="primary" :disabled="!selectedEvidenceId" @click="runAssetMatch">执行匹配</el-button>
                <el-button :disabled="!currentEvidence?.matched_asset_id && !selectedAssetId" @click="confirmMatchedAsset">确认绑定</el-button>
                <el-button @click="openCreateAsset">一键创建新资产</el-button>
              </el-space>
            </el-space>
          </el-card>

          <el-card class="asset-match-card" shadow="never">
            <template #header>
              <div class="section-header">
                <div class="section-title">指导书匹配</div>
                <div class="section-subtitle">基于证据文本、资产类型和核查关键词，建议当前证据对应的指导书条目。</div>
              </div>
            </template>
            <el-space direction="vertical" fill>
              <div class="match-status-row">
                <AppStatusTag kind="asset" :status="guidanceMatchStatusTag" />
                <span class="muted-text">匹配分数：{{ currentEvidence?.guidance_match_score ?? '-' }}</span>
              </div>
              <div class="meta-list compact">
                <span>指导书条目：{{ currentEvidence?.matched_guidance?.section_title || guidanceMatchReasons.section_title || '未匹配' }}</span>
                <span>章节路径：{{ currentEvidence?.matched_guidance?.section_path || guidanceMatchReasons.section_path || '未识别' }}</span>
                <span>指导书编码：{{ currentEvidence?.matched_guidance?.guidance_code || guidanceMatchReasons.guidance_code || '未识别' }}</span>
              </div>
              <div v-if="guidanceReasonList.length" class="reason-list">
                <div v-for="reason in guidanceReasonList" :key="reason" class="reason-item">- {{ reason }}</div>
              </div>
              <el-select v-model="selectedGuidanceId" clearable filterable placeholder="人工选择指导书条目">
                <el-option
                  v-for="item in guidanceItems"
                  :key="item.id"
                  :label="`${item.section_title} (${item.guidance_code})`"
                  :value="item.id"
                />
              </el-select>
              <el-space wrap>
                <el-button type="primary" :disabled="!selectedEvidenceId" @click="runGuidanceMatch">执行匹配</el-button>
                <el-button :disabled="!currentEvidence?.matched_guidance_id && !selectedGuidanceId" @click="confirmMatchedGuidance">确认绑定</el-button>
              </el-space>
              <el-alert
                v-if="!guidanceHistoryList.length"
                type="info"
                :closable="false"
                title="当前没有可展示的历史参考记录。"
              />
              <div v-else class="guidance-history-list">
                <div class="panel-label">历史人工记录参考（Top {{ guidanceHistoryList.length }})</div>
                <div v-for="item in guidanceHistoryList" :key="item.history_record_id" class="guidance-history-item">
                  <div class="guidance-history-item__head">
                    <span>{{ item.sheet_name }}</span>
                    <span class="muted-text">{{ item.asset_name || '未命名资产' }} / {{ item.compliance_status || '未标注状态' }}</span>
                  </div>
                  <div class="muted-text">匹配分数：{{ item.match_score }}</div>
                  <div class="muted-text">{{ getGuidanceHistorySummary(item.match_reason) }}</div>
                </div>
              </div>
            </el-space>
          </el-card>
        </el-card>

        <el-card class="review-column">
          <template #header>
            <div class="section-header">
              <div class="section-title">OCR 文本</div>
              <div class="section-subtitle">中栏保留原始 OCR 文本，用于和右侧字段修正结果逐项对照。</div>
            </div>
          </template>
          <el-scrollbar height="760px">
            <pre class="code-block">{{ ocrText }}</pre>
          </el-scrollbar>
        </el-card>

        <el-card class="review-column review-column--wide">
          <template #header>
            <div class="section-header">
              <div class="section-title">抽取字段与修正表单</div>
              <div class="section-subtitle">右栏聚焦 corrected_value、复核状态、复核意见和审计轨迹，是当前复核主战场。</div>
            </div>
          </template>
          <FieldReviewTable :fields="fields" @update="saveField" @review="markFieldReview" @audit="loadFieldAuditLogs" />
        </el-card>
      </div>

      <el-card v-if="auditLogs.length">
        <template #header>
          <div class="section-header">
            <div class="section-title">字段审计日志</div>
            <div class="section-subtitle">查看当前字段从保存到复核的轨迹，确保过程可回溯。</div>
          </div>
        </template>
        <el-timeline>
          <el-timeline-item v-for="log in auditLogs" :key="log.id" :timestamp="log.created_at">
            <div>{{ log.action }} / {{ log.reviewed_by || '未填写复核人' }}</div>
            <div class="muted-text">{{ log.review_comment || '无复核意见' }}</div>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <AssetFormDialog v-model="assetDialogVisible" :asset="editingAsset" mode="create" @submit="createSuggestedAsset" />
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import AppStatusTag from '@/components/AppStatusTag.vue'
import AssetFormDialog from '@/components/AssetFormDialog.vue'
import FieldReviewTable from '@/components/FieldReviewTable.vue'
import { createAsset, listAssets } from '@/api/assets'
import { listGuidanceItems } from '@/api/guidance'
import { confirmEvidenceAsset, confirmEvidenceGuidance, getOcrResult, listEvidenceFields, listEvidences, matchEvidenceAsset, matchEvidenceGuidance } from '@/api/evidences'
import { listFieldAuditLogs, reviewField, updateField } from '@/api/fields'
import { listRecords } from '@/api/records'
import type {
  Asset,
  AssetMatchReasons,
  AuditLog,
  Evidence,
  EvaluationRecord,
  ExtractedField,
  GuidanceItem,
  GuidanceMatchReasons,
  GuidanceMatchReason,
  MatchReasons,
} from '@/types/domain'

const props = defineProps<{ projectId: string; evidenceId?: string }>()
const route = useRoute()
const evidences = ref<Evidence[]>([])
const selectedEvidenceId = ref('')
const selectedAssetId = ref('')
const selectedGuidanceId = ref('')
const ocrText = ref('')
const fields = ref<ExtractedField[]>([])
const auditLogs = ref<AuditLog[]>([])
const records = ref<EvaluationRecord[]>([])
const assets = ref<Asset[]>([])
const guidanceItems = ref<GuidanceItem[]>([])
const assetDialogVisible = ref(false)
const editingAsset = ref<Asset | null>(null)

const currentEvidence = computed(() => evidences.value.find((item) => item.id === selectedEvidenceId.value) || null)
const relatedRecord = computed(() => records.value.find((item) => item.evidence_ids.includes(selectedEvidenceId.value)) || null)
const relatedRecordMissingFields = computed(() => {
  const reasons = relatedRecord.value?.match_reasons
  if (!reasons || typeof reasons !== 'object') return []
  const missing = (reasons as MatchReasons).missing_required_fields
  return Array.isArray(missing) ? missing : []
})
const testObjectAssets = computed(() => assets.value.filter((item) => item.asset_kind === 'test_object'))
const matchReasons = computed<AssetMatchReasons>(() => {
  const reasons = currentEvidence.value?.asset_match_reasons_json
  return reasons && typeof reasons === 'object' ? (reasons as AssetMatchReasons) : {}
})
const reasonList = computed(() => matchReasons.value.summary || [])
const guidanceMatchReasons = computed<GuidanceMatchReasons>(() => {
  const reasons = currentEvidence.value?.guidance_match_reasons_json
  return reasons && typeof reasons === 'object' ? (reasons as GuidanceMatchReasons) : {}
})
const guidanceReasonList = computed(() => guidanceMatchReasons.value.summary || [])
const guidanceHistoryList = computed(() => guidanceMatchReasons.value.top_history || [])
const guidanceMatchStatusTag = computed(() => {
  const status = currentEvidence.value?.guidance_match_status
  if (status === 'suggested') return 'pending'
  if (status === 'confirmed') return 'processed'
  if (status === 'unmatched') return 'failed'
  return 'pending'
})
const assetMatchStatusTag = computed(() => {
  const status = currentEvidence.value?.asset_match_status
  if (status === 'suggested') return 'pending'
  if (status === 'confirmed') return 'processed'
  if (status === 'unmatched') return 'failed'
  return 'pending'
})

async function loadEvidencesData() {
  const { data } = await listEvidences(props.projectId)
  evidences.value = data
  const queryEvidenceId = (route.query.evidenceId as string | undefined) || props.evidenceId
  selectedEvidenceId.value = queryEvidenceId || data[0]?.id || ''
}

async function loadAssetsData() {
  const { data } = await listAssets(props.projectId)
  assets.value = data
}

async function loadGuidanceData() {
  const { data } = await listGuidanceItems()
  guidanceItems.value = data.items || []
}

async function loadReviewData() {
  if (!selectedEvidenceId.value) {
    ocrText.value = '请先从证据中心上传并选择证据。'
    fields.value = []
    return
  }
  const [ocrResult, fieldsResult, recordsResult, evidencesResult, assetsResult, guidanceResult] = await Promise.all([
    getOcrResult(selectedEvidenceId.value).catch(() => ({ data: { full_text: '该证据尚未完成 OCR。' } })),
    listEvidenceFields(selectedEvidenceId.value).catch(() => ({ data: [] })),
    listRecords(props.projectId).catch(() => ({ data: [] })),
    listEvidences(props.projectId),
    listAssets(props.projectId),
    listGuidanceItems().catch(() => ({ data: { items: [] } })),
  ])
  ocrText.value = ocrResult.data.full_text || JSON.stringify(ocrResult.data, null, 2)
  fields.value = fieldsResult.data
  records.value = recordsResult.data
  evidences.value = evidencesResult.data
  assets.value = assetsResult.data
  guidanceItems.value = guidanceResult.data.items || []
  auditLogs.value = []
  selectedAssetId.value = currentEvidence.value?.matched_asset_id || ''
  selectedGuidanceId.value = currentEvidence.value?.matched_guidance_id || ''
}

async function saveField(fieldId: string, payload: Record<string, unknown>) {
  await updateField(fieldId, payload)
  ElMessage.success('字段更新成功')
  await loadReviewData()
}

async function markFieldReview(fieldId: string, payload: Record<string, unknown>) {
  if (!payload.status) {
    ElMessage.warning('请先选择复核状态')
    return
  }
  await reviewField(fieldId, {
    status: String(payload.status),
    corrected_value: (payload.corrected_value as string) || null,
    review_comment: (payload.review_comment as string) || null,
    reviewed_by: (payload.reviewed_by as string) || null,
  })
  ElMessage.success('字段复核成功')
  await loadReviewData()
}

async function loadFieldAuditLogs(fieldId: string) {
  const { data } = await listFieldAuditLogs(fieldId)
  auditLogs.value = data
}

async function runAssetMatch() {
  if (!selectedEvidenceId.value) return
  await matchEvidenceAsset(selectedEvidenceId.value, true)
  ElMessage.success('测试对象匹配完成')
  await loadReviewData()
}

async function confirmMatchedAsset() {
  if (!selectedEvidenceId.value) return
  await confirmEvidenceAsset(selectedEvidenceId.value, selectedAssetId.value || currentEvidence.value?.matched_asset_id || null)
  ElMessage.success('测试对象绑定成功')
  await loadReviewData()
}

async function runGuidanceMatch() {
  if (!selectedEvidenceId.value) return
  await matchEvidenceGuidance(selectedEvidenceId.value, true)
  ElMessage.success('指导书匹配完成')
  await loadReviewData()
}

async function confirmMatchedGuidance() {
  if (!selectedEvidenceId.value) return
  await confirmEvidenceGuidance(selectedEvidenceId.value, selectedGuidanceId.value || currentEvidence.value?.matched_guidance_id || null)
  ElMessage.success('指导书绑定成功')
  await loadReviewData()
}

function getGuidanceHistorySummary(reason: GuidanceMatchReason | Record<string, unknown>) {
  const summary = 'summary' in reason ? reason.summary : undefined
  return Array.isArray(summary) && summary.length ? summary.join('；') : '无匹配说明'
}

function openCreateAsset() {
  editingAsset.value = {
    id: '',
    project_id: props.projectId,
    asset_kind: 'test_object',
    category: matchReasons.value.suggested_asset_type || 'device',
    category_label: matchReasons.value.suggested_asset_type || '设备资产',
    batch_no: null,
    filename: matchReasons.value.suggested_asset_name || currentEvidence.value?.device || '',
    primary_ip: String((matchReasons.value.signals as Record<string, unknown> | undefined)?.device_ip || ''),
    file_ext: null,
    mime_type: null,
    relative_path: 'assets/device.txt',
    absolute_path: null,
    file_size: null,
    file_sha256: null,
    file_mtime: null,
    source: 'manual',
    ingest_status: 'pending',
    created_at: '',
    updated_at: '',
  }
  assetDialogVisible.value = true
}

async function createSuggestedAsset(payload: Record<string, unknown>) {
  const { data } = await createAsset(props.projectId, payload as never)
  assetDialogVisible.value = false
  selectedAssetId.value = data.id
  ElMessage.success('测试对象资产创建成功')
  await confirmMatchedAsset()
}

onMounted(async () => {
  await loadEvidencesData()
  await loadAssetsData()
  await loadGuidanceData()
  await loadReviewData()
})
</script>

<style scoped>
.review-grid {
  display: grid;
  grid-template-columns: minmax(260px, 0.9fr) minmax(340px, 1.05fr) minmax(430px, 1.45fr);
  gap: 16px;
}

.review-column {
  min-height: 100%;
}

.review-column--wide {
  min-width: 0;
}

.preview-placeholder {
  display: grid;
  place-items: center;
  min-height: 240px;
  margin-bottom: 16px;
  padding: 18px;
  border-radius: 18px;
  border: 1px dashed var(--workspace-border-strong);
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.98), rgba(237, 244, 252, 0.98));
  text-align: center;
}

.preview-placeholder__icon {
  padding: 10px 14px;
  border-radius: 999px;
  background: #0f172a;
  color: #f8fafc;
  font-size: 12px;
  letter-spacing: 0.08em;
  font-weight: 700;
}

.preview-placeholder__title {
  margin-top: 14px;
  font-size: 16px;
  font-weight: 800;
  color: var(--workspace-text);
}

.preview-placeholder__text {
  margin-top: 10px;
  color: var(--workspace-text-muted);
  line-height: 1.7;
}

.review-meta-panel {
  margin-bottom: 16px;
}

.meta-descriptions {
  margin-top: 8px;
}

.asset-match-card {
  margin-top: 16px;
}

.match-status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.reason-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.reason-item {
  color: var(--workspace-text-muted);
  line-height: 1.6;
}

.compact {
  gap: 4px;
}

.guidance-history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.guidance-history-item {
  padding: 10px 12px;
  border: 1px solid var(--workspace-border-soft);
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.86);
}

.guidance-history-item__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}

@media (max-width: 1400px) {
  .review-grid {
    grid-template-columns: 1fr;
  }
}
</style>
