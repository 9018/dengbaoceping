<template>
  <el-tag :type="tagType" effect="light" round class="app-status-tag" :class="[`app-status-tag--${tagType || 'info'}`]">
    <span class="app-status-tag__dot" />
    <span>{{ label }}</span>
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getStatusLabel, getStatusTagType, type StatusKind } from '@/utils/status'

const props = defineProps<{
  kind: StatusKind
  status?: string | null
}>()

const label = computed(() => getStatusLabel(props.kind, props.status))
const tagType = computed(() => getStatusTagType(props.kind, props.status))
</script>

<style scoped>
.app-status-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding-inline: 12px;
  font-weight: 700;
  border-width: 1px;
}

.app-status-tag__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.85;
}

.app-status-tag--primary {
  background: rgba(37, 99, 235, 0.12);
}

.app-status-tag--success {
  background: rgba(5, 150, 105, 0.12);
}

.app-status-tag--warning {
  background: rgba(217, 119, 6, 0.12);
}

.app-status-tag--danger {
  background: rgba(220, 38, 38, 0.1);
}

.app-status-tag--info {
  background: rgba(100, 116, 139, 0.1);
}
</style>
