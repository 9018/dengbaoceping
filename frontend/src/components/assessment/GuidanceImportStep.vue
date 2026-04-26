<template>
  <WorkflowStepCard title="导入指导书" summary="给模板项补充依据、检查点、证据要求和记录建议。">
    <div class="step-stack">
      <el-space wrap>
        <el-button type="primary" @click="$emit('import')">导入指导书</el-button>
        <el-button @click="$emit('refresh')">刷新状态</el-button>
      </el-space>
      <pre v-if="summary" class="step-pre">{{ JSON.stringify(summary, null, 2) }}</pre>
    </div>
  </WorkflowStepCard>
</template>

<script setup lang="ts">
import WorkflowStepCard from '@/components/workflow/WorkflowStepCard.vue'

defineProps<{ summary?: Record<string, unknown> | null }>()
defineEmits<{ import: []; refresh: [] }>()
</script>

<style scoped>
.step-stack { display: flex; flex-direction: column; gap: 12px; }
.step-pre { margin: 0; white-space: pre-wrap; }
</style>
