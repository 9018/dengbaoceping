<template>
  <AppShell :project-id="projectId" title="识别复核" subtitle="展示 OCR 文本和字段列表，支持 corrected_value 修改与 review 状态标记">
    <el-space direction="vertical" fill size="16">
      <el-card>
        <template #header>
          <div class="toolbar">
            <span>证据选择</span>
            <el-button @click="loadReviewData">刷新</el-button>
          </div>
        </template>
        <el-select v-model="selectedEvidenceId" placeholder="请选择证据" style="width: 360px" @change="loadReviewData">
          <el-option v-for="item in evidences" :key="item.id" :label="`${item.title} (${item.device || '未绑定设备'})`" :value="item.id" />
        </el-select>
      </el-card>

      <el-row :gutter="16">
        <el-col :span="10">
          <el-card>
            <template #header>
              <span>OCR 文本</span>
            </template>
            <el-scrollbar height="540px">
              <pre class="ocr-text">{{ ocrText }}</pre>
            </el-scrollbar>
          </el-card>
        </el-col>
        <el-col :span="14">
          <el-card>
            <template #header>
              <span>ExtractedField 列表</span>
            </template>
            <FieldReviewTable :fields="fields" @update="saveField" @review="markFieldReview" @audit="loadFieldAuditLogs" />
          </el-card>
        </el-col>
      </el-row>

      <el-card v-if="auditLogs.length">
        <template #header>
          <span>字段审计日志</span>
        </template>
        <el-timeline>
          <el-timeline-item v-for="log in auditLogs" :key="log.id" :timestamp="log.created_at">
            <div>{{ log.action }} / {{ log.reviewed_by || '未填写复核人' }}</div>
            <div class="timeline-comment">{{ log.review_comment || '无复核意见' }}</div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </el-space>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import FieldReviewTable from '@/components/FieldReviewTable.vue'
import { listEvidences, getOcrResult, listEvidenceFields } from '@/api/evidences'
import { listFieldAuditLogs, reviewField, updateField } from '@/api/fields'
import type { AuditLog, Evidence, ExtractedField } from '@/types/domain'

const props = defineProps<{ projectId: string; evidenceId?: string }>()
const route = useRoute()
const evidences = ref<Evidence[]>([])
const selectedEvidenceId = ref<string>('')
const ocrText = ref('')
const fields = ref<ExtractedField[]>([])
const auditLogs = ref<AuditLog[]>([])

async function loadEvidencesData() {
  const { data } = await listEvidences(props.projectId)
  evidences.value = data
  const queryEvidenceId = (route.query.evidenceId as string | undefined) || props.evidenceId
  selectedEvidenceId.value = queryEvidenceId || data[0]?.id || ''
}

async function loadReviewData() {
  if (!selectedEvidenceId.value) {
    ocrText.value = '请先从证据管理页上传并选择证据。'
    fields.value = []
    return
  }
  const [ocrResult, fieldsResult] = await Promise.all([
    getOcrResult(selectedEvidenceId.value).catch(() => ({ data: { full_text: '该证据尚未完成 OCR。' } })),
    listEvidenceFields(selectedEvidenceId.value).catch(() => ({ data: [] })),
  ])
  ocrText.value = ocrResult.data.full_text || JSON.stringify(ocrResult.data, null, 2)
  fields.value = fieldsResult.data
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
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ocr-text {
  white-space: pre-wrap;
  margin: 0;
  font-family: monospace;
  line-height: 1.6;
}

.timeline-comment {
  color: #909399;
  margin-top: 4px;
}
</style>
