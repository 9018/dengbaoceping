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
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import AppStatusTag from '@/components/AppStatusTag.vue'
import FieldReviewTable from '@/components/FieldReviewTable.vue'
import { getOcrResult, listEvidenceFields, listEvidences } from '@/api/evidences'
import { listFieldAuditLogs, reviewField, updateField } from '@/api/fields'
import { listRecords } from '@/api/records'
import type { AuditLog, Evidence, EvaluationRecord, ExtractedField, MatchReasons } from '@/types/domain'

const props = defineProps<{ projectId: string; evidenceId?: string }>()
const route = useRoute()
const evidences = ref<Evidence[]>([])
const selectedEvidenceId = ref('')
const ocrText = ref('')
const fields = ref<ExtractedField[]>([])
const auditLogs = ref<AuditLog[]>([])
const records = ref<EvaluationRecord[]>([])

const currentEvidence = computed(() => evidences.value.find((item) => item.id === selectedEvidenceId.value) || null)
const relatedRecord = computed(() => records.value.find((item) => item.evidence_ids.includes(selectedEvidenceId.value)) || null)
const relatedRecordMissingFields = computed(() => {
  const reasons = relatedRecord.value?.match_reasons
  if (!reasons || typeof reasons !== 'object') return []
  const missing = (reasons as MatchReasons).missing_required_fields
  return Array.isArray(missing) ? missing : []
})

async function loadEvidencesData() {
  const { data } = await listEvidences(props.projectId)
  evidences.value = data
  const queryEvidenceId = (route.query.evidenceId as string | undefined) || props.evidenceId
  selectedEvidenceId.value = queryEvidenceId || data[0]?.id || ''
}

async function loadReviewData() {
  if (!selectedEvidenceId.value) {
    ocrText.value = '请先从证据中心上传并选择证据。'
    fields.value = []
    return
  }
  const [ocrResult, fieldsResult, recordsResult] = await Promise.all([
    getOcrResult(selectedEvidenceId.value).catch(() => ({ data: { full_text: '该证据尚未完成 OCR。' } })),
    listEvidenceFields(selectedEvidenceId.value).catch(() => ({ data: [] })),
    listRecords(props.projectId).catch(() => ({ data: [] })),
  ])
  ocrText.value = ocrResult.data.full_text || JSON.stringify(ocrResult.data, null, 2)
  fields.value = fieldsResult.data
  records.value = recordsResult.data
  auditLogs.value = []
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

onMounted(async () => {
  await loadEvidencesData()
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

@media (max-width: 1400px) {
  .review-grid {
    grid-template-columns: 1fr;
  }
}
</style>
