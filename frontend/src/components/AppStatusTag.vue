<template>
  <el-tag :type="tagType" effect="light" round class="app-status-tag">
    {{ label }}
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
  font-weight: 600;
  border-radius: 999px;
  padding-inline: 10px;
}
</style>
