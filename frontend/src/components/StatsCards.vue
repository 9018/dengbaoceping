<template>
  <el-row :gutter="16">
    <el-col v-for="item in items" :key="item.label" :xs="24" :sm="12" :md="12" :lg="6">
      <StatCard
        :label="item.label"
        :value="item.value"
        :tip="item.tip"
        :clickable="Boolean(item.to)"
        :tone="item.tone || 'default'"
        @select="emitSelect(item)"
      />
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import StatCard from '@/components/StatCard.vue'

export interface StatsCardItem {
  label: string
  value: string | number
  tip?: string
  to?: string
  tone?: 'default' | 'primary' | 'success' | 'warning'
}

defineProps<{
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
