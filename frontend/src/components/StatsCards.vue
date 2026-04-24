<template>
  <div class="stats-cards">
    <div v-for="item in items" :key="item.label" class="stats-cards__item">
      <StatCard
        :label="item.label"
        :value="item.value"
        :tip="item.tip"
        :clickable="Boolean(item.to)"
        :tone="item.tone || 'default'"
        @select="emitSelect(item)"
      />
    </div>
  </div>
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

<style scoped>
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.stats-cards__item {
  min-width: 0;
}
</style>
