<template>
  <WorkflowStepCard title="创建项目资产" summary="维护项目内测试对象，作为生成项目测评表的抓手。">
    <div class="step-stack">
      <el-space wrap>
        <el-button type="primary" @click="$emit('create')">新增资产</el-button>
        <el-button @click="$emit('refresh')">刷新资产</el-button>
      </el-space>
      <el-table :data="assets" border>
        <el-table-column prop="filename" label="资产名称" min-width="180" />
        <el-table-column prop="category" label="分类标识" width="160" />
        <el-table-column prop="category_label" label="分类名称" min-width="160" />
        <el-table-column prop="primary_ip" label="主 IP" min-width="140" />
      </el-table>
    </div>
  </WorkflowStepCard>
</template>

<script setup lang="ts">
import WorkflowStepCard from '@/components/workflow/WorkflowStepCard.vue'

defineProps<{ assets: Array<Record<string, any>> }>()
defineEmits<{ create: []; refresh: [] }>()
</script>

<style scoped>
.step-stack { display: flex; flex-direction: column; gap: 12px; }
</style>
