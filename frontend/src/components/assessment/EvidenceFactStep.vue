<template>
  <WorkflowStepCard title="识别页面类型和证据事实" summary="对当前证据执行页面分类和事实抽取，沉淀可写入草稿的事实集合。">
    <div class="step-stack">
      <el-space wrap>
        <el-button type="primary" :disabled="!selectedEvidenceId" @click="$emit('extract')">识别事实</el-button>
        <el-button @click="$emit('refresh')">刷新事实</el-button>
      </el-space>
      <div class="meta-grid">
        <div class="soft-item">
          <div class="soft-label">页面类型</div>
          <div class="soft-value">{{ result?.page_type || '-' }}</div>
        </div>
        <div class="soft-item">
          <div class="soft-label">置信度</div>
          <div class="soft-value">{{ result?.confidence ?? '-' }}</div>
        </div>
      </div>
      <div v-if="result?.reason" class="step-reason">{{ result.reason }}</div>
      <div v-if="result?.matched_keywords?.length" class="tag-group">
        <el-tag v-for="keyword in result.matched_keywords" :key="keyword" effect="plain">{{ keyword }}</el-tag>
      </div>
      <el-table :data="result?.facts || []" border>
        <el-table-column prop="fact_name" label="事实名称" min-width="180" />
        <el-table-column prop="normalized_value" label="归一化值" min-width="220" show-overflow-tooltip />
        <el-table-column prop="fact_group" label="分组" width="120" />
        <el-table-column prop="confidence" label="置信度" width="120" />
      </el-table>
    </div>
  </WorkflowStepCard>
</template>

<script setup lang="ts">
import type { EvidenceFactExtractionResult } from '@/types/domain'
import WorkflowStepCard from '@/components/workflow/WorkflowStepCard.vue'

defineProps<{
  selectedEvidenceId: string
  result?: EvidenceFactExtractionResult | null
}>()

defineEmits<{
  extract: []
  refresh: []
}>()
</script>

<style scoped>
.step-stack { display: flex; flex-direction: column; gap: 12px; }
.meta-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.soft-item { padding: 12px; border-radius: 12px; background: rgba(248, 250, 252, 0.92); border: 1px solid var(--workspace-border-soft); }
.soft-label { font-size: 12px; color: var(--workspace-text-muted); }
.soft-value { margin-top: 6px; font-weight: 700; color: var(--workspace-text); }
.step-reason { color: var(--workspace-text-secondary); line-height: 1.7; }
.tag-group { display: flex; flex-wrap: wrap; gap: 8px; }
</style>
