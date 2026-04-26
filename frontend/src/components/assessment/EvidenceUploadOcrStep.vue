<template>
  <WorkflowStepCard title="上传截图并 OCR" summary="上传项目截图证据，执行 OCR 并准备进入事实识别。">
    <div class="step-stack">
      <el-space wrap>
        <el-button type="primary" @click="$emit('upload')">上传证据</el-button>
        <el-button :disabled="!selectedEvidenceId" @click="$emit('ocr')">执行 OCR</el-button>
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
      <el-table :data="evidences" border>
        <el-table-column prop="title" label="证据标题" min-width="220" />
        <el-table-column prop="device" label="关联资产" min-width="160" />
        <el-table-column prop="ocr_status" label="OCR 状态" width="140" />
        <el-table-column prop="updated_at" label="更新时间" min-width="180" />
      </el-table>
      <pre v-if="ocrText" class="step-pre">{{ ocrText }}</pre>
    </div>
  </WorkflowStepCard>
</template>

<script setup lang="ts">
import type { Evidence } from '@/types/domain'
import WorkflowStepCard from '@/components/workflow/WorkflowStepCard.vue'

defineProps<{
  evidences: Evidence[]
  selectedEvidenceId: string
  ocrText?: string
}>()

defineEmits<{
  upload: []
  ocr: []
  refresh: []
  selectEvidence: [value: string]
}>()
</script>

<style scoped>
.step-stack { display: flex; flex-direction: column; gap: 12px; }
.step-pre { margin: 0; white-space: pre-wrap; max-height: 280px; overflow: auto; }
</style>
