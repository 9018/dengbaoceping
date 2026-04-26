<template>
  <WorkflowStepCard title="生成 D/E 列草稿" summary="结合模板、指导书、历史记录与证据事实，生成待人工确认的记录草稿。">
    <div class="step-stack">
      <el-space wrap>
        <el-button type="primary" :disabled="!itemId || !evidenceId" @click="$emit('generate')">生成草稿</el-button>
        <el-button @click="$emit('refresh')">刷新草稿</el-button>
      </el-space>
      <div class="meta-grid">
        <div class="soft-item">
          <div class="soft-label">草稿符合情况</div>
          <div class="soft-value">{{ draft?.draft_compliance_result || '-' }}</div>
        </div>
        <div class="soft-item">
          <div class="soft-label">置信度</div>
          <div class="soft-value">{{ draft?.confidence ?? '-' }}</div>
        </div>
      </div>
      <div v-if="draft?.reason?.length" class="reason-list">
        <div v-for="reason in draft.reason" :key="reason" class="reason-item">- {{ reason }}</div>
      </div>
      <div v-if="draft?.missing_evidence?.length" class="reason-list">
        <div v-for="reason in draft.missing_evidence" :key="reason" class="reason-item reason-item--warn">- 缺失：{{ reason }}</div>
      </div>
      <pre v-if="draft?.draft_record_text" class="step-pre">{{ draft.draft_record_text }}</pre>
    </div>
  </WorkflowStepCard>
</template>

<script setup lang="ts">
import type { ProjectAssessmentDraftResult } from '@/types/domain'
import WorkflowStepCard from '@/components/workflow/WorkflowStepCard.vue'

defineProps<{
  itemId: string
  evidenceId: string
  draft?: ProjectAssessmentDraftResult | null
}>()

defineEmits<{
  generate: []
  refresh: []
}>()
</script>

<style scoped>
.step-stack { display: flex; flex-direction: column; gap: 12px; }
.meta-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.soft-item { padding: 12px; border-radius: 12px; background: rgba(248, 250, 252, 0.92); border: 1px solid var(--workspace-border-soft); }
.soft-label { font-size: 12px; color: var(--workspace-text-muted); }
.soft-value { margin-top: 6px; font-weight: 700; color: var(--workspace-text); }
.reason-list { display: flex; flex-direction: column; gap: 6px; }
.reason-item { color: var(--workspace-text-secondary); }
.reason-item--warn { color: #b45309; }
.step-pre { margin: 0; white-space: pre-wrap; max-height: 320px; overflow: auto; }
</style>
