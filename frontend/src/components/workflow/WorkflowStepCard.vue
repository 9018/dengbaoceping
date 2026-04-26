<template>
  <el-card shadow="never">
    <template #header>
      <div>
        <div style="font-weight: 700">{{ title }}</div>
        <div style="margin-top: 4px; color: var(--workspace-text-muted); font-size: 13px">{{ summary }}</div>
      </div>
    </template>
    <slot />
  </el-card>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  summary: string
}>()
</script>
