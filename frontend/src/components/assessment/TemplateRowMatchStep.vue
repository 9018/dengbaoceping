<template>
  <WorkflowStepCard title="匹配项目测评表行" summary="把证据先匹配到模板候选，再映射到当前项目内的测评表行。">
    <div class="step-stack">
      <el-space wrap>
        <el-button type="primary" :disabled="!selectedEvidenceId" @click="$emit('match')">匹配测评项</el-button>
        <el-button @click="$emit('refresh')">刷新候选</el-button>
      </el-space>
      <div class="meta-grid">
        <div class="soft-item">
          <div class="soft-label">首选候选</div>
          <div class="soft-value">{{ result?.matched_project_assessment_item?.item_code || '-' }}</div>
        </div>
        <div class="soft-item">
          <div class="soft-label">置信度</div>
          <div class="soft-value">{{ result?.confidence ?? '-' }}</div>
        </div>
      </div>
      <div v-if="result?.reason?.length" class="reason-list">
        <div v-for="reason in result.reason" :key="reason" class="reason-item">- {{ reason }}</div>
      </div>
      <el-table :data="result?.candidates || []" border highlight-current-row @row-click="handleRowClick">
        <el-table-column prop="item_code" label="编号" width="120" />
        <el-table-column prop="sheet_name" label="Sheet" min-width="160" />
        <el-table-column prop="control_point" label="控制点" min-width="220" show-overflow-tooltip />
        <el-table-column prop="item_text" label="测评项" min-width="220" show-overflow-tooltip />
        <el-table-column prop="score" label="分数" width="100" />
      </el-table>
    </div>
  </WorkflowStepCard>
</template>

<script setup lang="ts">
import type { ProjectAssessmentItemMatchCandidate, ProjectAssessmentItemMatchResult } from '@/types/domain'
import WorkflowStepCard from '@/components/workflow/WorkflowStepCard.vue'

const props = defineProps<{
  selectedEvidenceId: string
  result?: ProjectAssessmentItemMatchResult | null
}>()

const emit = defineEmits<{
  match: []
  refresh: []
  selectCandidate: [value: string]
}>()

function handleRowClick(candidate: ProjectAssessmentItemMatchCandidate) {
  if (!candidate?.project_assessment_item_id) return
  emit('selectCandidate', candidate.project_assessment_item_id)
}
</script>

<style scoped>
.step-stack { display: flex; flex-direction: column; gap: 12px; }
.meta-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.soft-item { padding: 12px; border-radius: 12px; background: rgba(248, 250, 252, 0.92); border: 1px solid var(--workspace-border-soft); }
.soft-label { font-size: 12px; color: var(--workspace-text-muted); }
.soft-value { margin-top: 6px; font-weight: 700; color: var(--workspace-text); }
.reason-list { display: flex; flex-direction: column; gap: 6px; }
.reason-item { color: var(--workspace-text-secondary); }
</style>
