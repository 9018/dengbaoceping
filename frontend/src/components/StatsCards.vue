<template>
  <el-row :gutter="16">
    <el-col v-for="item in items" :key="item.label" :xs="24" :sm="12" :md="6">
      <el-card shadow="hover" class="stats-card" :class="{ 'stats-card--clickable': Boolean(item.to) }" @click="emitSelect(item)">
        <div class="stats-card__label">{{ item.label }}</div>
        <div class="stats-card__value">{{ item.value }}</div>
        <div v-if="item.tip" class="stats-card__tip">{{ item.tip }}</div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
interface StatsCardItem {
  label: string
  value: string | number
  tip?: string
  to?: string
}

const props = defineProps<{
  items: StatsCardItem[]
}>()

const emit = defineEmits<{
  (e: 'select', item: StatsCardItem): void
}>()

function emitSelect(item: StatsCardItem) {
  if (!item.to) return
  emit('select', item)
}
</script>

<style scoped>
.stats-card {
  margin-bottom: 16px;
}

.stats-card--clickable {
  cursor: pointer;
}

.stats-card__label {
  color: #909399;
  font-size: 13px;
}

.stats-card__value {
  margin-top: 12px;
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.stats-card__tip {
  margin-top: 8px;
  color: #67c23a;
  font-size: 12px;
}
</style>
