<template>
  <WorkflowStepCard title="人工确认并写回项目测评表" summary="对草稿内容和符合情况做最终确认，并写回项目测评表行。">
    <div class="step-stack">
      <el-form label-width="96px">
        <el-form-item label="符合情况">
          <el-input :model-value="complianceResult" @input="$emit('update:complianceResult', $event)" />
        </el-form-item>
        <el-form-item label="结果记录">
          <el-input :model-value="recordText" type="textarea" :rows="8" @input="$emit('update:recordText', $event)" />
        </el-form-item>
        <el-form-item label="复核意见">
          <el-input :model-value="reviewComment" type="textarea" :rows="3" @input="$emit('update:reviewComment', $event)" />
        </el-form-item>
        <el-form-item label="复核人">
          <el-input :model-value="reviewedBy" @input="$emit('update:reviewedBy', $event)" />
        </el-form-item>
      </el-form>
      <el-space wrap>
        <el-button type="primary" :disabled="!itemId" @click="$emit('confirm')">确认写回</el-button>
        <el-button @click="$emit('refresh')">刷新条目</el-button>
      </el-space>
    </div>
  </WorkflowStepCard>
</template>

<script setup lang="ts">
import WorkflowStepCard from '@/components/workflow/WorkflowStepCard.vue'

defineProps<{
  itemId: string
  recordText: string
  complianceResult: string
  reviewComment: string
  reviewedBy: string
}>()

defineEmits<{
  confirm: []
  refresh: []
  'update:recordText': [value: string]
  'update:complianceResult': [value: string]
  'update:reviewComment': [value: string]
  'update:reviewedBy': [value: string]
}>()
</script>

<style scoped>
.step-stack { display: flex; flex-direction: column; gap: 12px; }
</style>
