<template>
  <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 16px">
    <el-button v-if="showPrevious" @click="$emit('previous')">上一步</el-button>
    <el-button type="primary" :disabled="disabled" @click="$emit('next')">下一步</el-button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  disabled?: boolean
  showPrevious?: boolean
}>()

defineEmits<{
  previous: []
  next: []
}>()
</script>
