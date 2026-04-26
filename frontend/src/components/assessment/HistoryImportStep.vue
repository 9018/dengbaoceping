<template>
  <WorkflowStepCard title="导入历史人工测评记录" summary="沉淀写法样本和符合情况样本。">
    <div class="step-stack">
      <input type="file" accept=".xlsx,.xls" @change="onFileChange" />
      <el-space wrap>
        <el-button type="primary" :disabled="!file" @click="submit">导入历史记录</el-button>
        <el-button @click="$emit('refresh')">刷新状态</el-button>
      </el-space>
      <pre v-if="summary" class="step-pre">{{ JSON.stringify(summary, null, 2) }}</pre>
    </div>
  </WorkflowStepCard>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import WorkflowStepCard from '@/components/workflow/WorkflowStepCard.vue'

defineProps<{ summary?: Record<string, unknown> | null }>()
const emit = defineEmits<{ import: [file: File]; refresh: [] }>()
const file = ref<File | null>(null)

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  file.value = input.files?.[0] || null
}

function submit() {
  if (!file.value) return
  emit('import', file.value)
}
</script>

<style scoped>
.step-stack { display: flex; flex-direction: column; gap: 12px; }
.step-pre { margin: 0; white-space: pre-wrap; }
</style>
