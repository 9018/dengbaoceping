<template>
  <el-steps :active="active" finish-status="success" align-center>
    <el-step v-for="step in steps" :key="step.key" :title="step.title" :description="step.summary" />
  </el-steps>
</template>

<script setup lang="ts">
defineProps<{
  active: number
  steps: Array<{
    key: string
    title: string
    summary: string
  }>
}>()
</script>
