<template>
  <WorkflowStepCard title="生成项目测评表" summary="按资产类型复制主模板项，形成项目内待填写测评表。">
    <div class="step-stack">
      <el-select :model-value="selectedAssetId" placeholder="选择资产" style="width: 320px" @change="$emit('selectAsset', $event)">
        <el-option v-for="asset in assets" :key="asset.id" :label="asset.filename" :value="asset.id" />
      </el-select>
      <el-space wrap>
        <el-button type="primary" :disabled="!selectedAssetId" @click="$emit('generate')">生成测评表</el-button>
        <el-button @click="$emit('refresh')">刷新测评表</el-button>
      </el-space>
      <el-table :data="tables" border>
        <el-table-column prop="name" label="测评表名称" min-width="220" />
        <el-table-column prop="status" label="状态" width="140" />
        <el-table-column prop="item_count" label="条目数" width="120" />
      </el-table>
    </div>
  </WorkflowStepCard>
</template>

<script setup lang="ts">
import WorkflowStepCard from '@/components/workflow/WorkflowStepCard.vue'

defineProps<{
  assets: Array<Record<string, any>>
  tables: Array<Record<string, any>>
  selectedAssetId: string
}>()

defineEmits<{ selectAsset: [value: string]; generate: []; refresh: [] }>()
</script>

<style scoped>
.step-stack { display: flex; flex-direction: column; gap: 12px; }
</style>
