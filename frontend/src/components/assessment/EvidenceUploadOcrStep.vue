<template>
  <WorkflowStepCard title="上传截图并 OCR" summary="上传项目截图证据，执行 OCR 并准备进入事实识别。">
    <div class="step-stack">
      <el-space wrap>
        <el-button type="primary" @click="$emit('upload')">上传证据</el-button>
        <el-button :disabled="!selectedEvidenceId" @click="$emit('ocr', false)">执行 OCR</el-button>
        <el-button :disabled="!selectedEvidenceId" @click="$emit('ocr', true)">强制重跑 OCR</el-button>
        <el-button @click="$emit('refresh')">刷新证据</el-button>
      </el-space>
      <el-select
        :model-value="selectedEvidenceId"
        placeholder="选择证据"
        style="width: 360px"
        filterable
        @change="$emit('selectEvidence', $event)"
      >
        <el-option v-for="evidence in evidences" :key="evidence.id" :label="evidence.title" :value="evidence.id" />
      </el-select>
      <div v-if="ocrHealth" class="ocr-health-grid">
        <div class="soft-panel">
          <div class="panel-label">OCR Provider</div>
          <div class="panel-value">{{ ocrHealth.provider_name }}</div>
          <div class="panel-meta">Adapter：{{ ocrHealth.adapter || '-' }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">健康状态</div>
          <div class="panel-value">{{ ocrHealth.status }}</div>
          <div class="panel-meta">可执行：{{ ocrHealth.can_run_ocr ? '是' : '否' }}</div>
        </div>
      </div>
      <el-alert
        v-if="ocrHealth?.error?.message"
        :title="ocrHealth.error.message"
        :description="ocrHealth.error.code"
        type="warning"
        show-icon
        :closable="false"
      />
      <el-table :data="evidences" border>
        <el-table-column prop="title" label="证据标题" min-width="220" />
        <el-table-column prop="device" label="关联资产" min-width="160" />
        <el-table-column label="OCR 状态" width="160">
          <template #default="scope">
            <AppStatusTag kind="ocr" :status="scope.row.ocr_status" />
          </template>
        </el-table-column>
        <el-table-column label="Provider" width="130">
          <template #default="scope">
            {{ scope.row.ocr_provider || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="错误信息" min-width="220" show-overflow-tooltip>
          <template #default="scope">
            {{ scope.row.ocr_error_message || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" min-width="180" />
      </el-table>
      <el-input
        v-model="manualOcrTextModel"
        type="textarea"
        :rows="6"
        placeholder="OCR 不可用或识别失败时，可在这里手工录入文本"
      />
      <el-space wrap>
        <el-button :disabled="!selectedEvidenceId || !manualOcrTextModel.trim()" @click="$emit('saveManualOcr', manualOcrTextModel)">
          保存手工 OCR
        </el-button>
        <span class="step-hint">支持失败回填，也支持 warning 场景下直接修正文本。</span>
      </el-space>
      <pre v-if="ocrText" class="step-pre">{{ ocrText }}</pre>
      <pre v-if="ocrErrorDetails" class="step-pre step-pre--danger">{{ ocrErrorDetails }}</pre>
    </div>
  </WorkflowStepCard>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Evidence, OcrHealth } from '@/types/domain'
import AppStatusTag from '@/components/AppStatusTag.vue'
import WorkflowStepCard from '@/components/workflow/WorkflowStepCard.vue'

const props = defineProps<{
  evidences: Evidence[]
  selectedEvidenceId: string
  ocrText?: string
  ocrHealth?: OcrHealth | null
}>()

const manualOcrTextModel = ref('')

const selectedEvidence = computed(() => props.evidences.find((item) => item.id === props.selectedEvidenceId) || null)
const ocrErrorDetails = computed(() => {
  const error = selectedEvidence.value?.ocr_error_json
  if (!error) return ''
  return JSON.stringify(error, null, 2)
})

watch(
  () => props.selectedEvidenceId,
  () => {
    manualOcrTextModel.value = selectedEvidence.value?.text_content || ''
  },
  { immediate: true },
)

defineEmits<{
  upload: []
  ocr: [force?: boolean]
  refresh: []
  selectEvidence: [value: string]
  saveManualOcr: [text: string]
}>()
</script>

<style scoped>
.step-stack { display: flex; flex-direction: column; gap: 12px; }
.step-pre { margin: 0; white-space: pre-wrap; max-height: 280px; overflow: auto; }
.step-pre--danger { color: #b91c1c; background: rgba(248, 113, 113, 0.08); padding: 12px; border-radius: 12px; }
.ocr-health-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.step-hint { color: var(--el-text-color-secondary); font-size: 13px; }
</style>
