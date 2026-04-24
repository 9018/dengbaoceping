<template>
  <el-card shadow="hover" class="stat-card" :class="[`stat-card--${tone}`, { 'stat-card--clickable': clickable }]" @click="handleClick">
    <div class="stat-card__head">
      <div>
        <div class="stat-card__label">{{ label }}</div>
        <div v-if="tip" class="stat-card__tip">{{ tip }}</div>
      </div>
      <div class="stat-card__dot" />
    </div>
    <div class="stat-card__value">{{ value }}</div>
  </el-card>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    label: string
    value: string | number
    tip?: string
    clickable?: boolean
    tone?: 'default' | 'primary' | 'success' | 'warning'
  }>(),
  {
    tip: '',
    clickable: false,
    tone: 'default',
  },
)

const emit = defineEmits<{
  (e: 'select'): void
}>()

function handleClick() {
  if (!props.clickable) return
  emit('select')
}
</script>

<style scoped>
.stat-card {
  border: 1px solid #e5eaf3;
  border-radius: 18px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-card--clickable {
  cursor: pointer;
}

.stat-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.stat-card__label {
  color: #5b6474;
  font-size: 13px;
  font-weight: 600;
}

.stat-card__tip {
  margin-top: 6px;
  color: #8a94a6;
  font-size: 12px;
}

.stat-card__value {
  margin-top: 18px;
  font-size: 32px;
  line-height: 1;
  font-weight: 700;
  color: #111827;
}

.stat-card__dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #94a3b8;
  box-shadow: 0 0 0 6px rgba(148, 163, 184, 0.14);
}

.stat-card--primary .stat-card__dot {
  background: #3b82f6;
  box-shadow: 0 0 0 6px rgba(59, 130, 246, 0.16);
}

.stat-card--success .stat-card__dot {
  background: #10b981;
  box-shadow: 0 0 0 6px rgba(16, 185, 129, 0.16);
}

.stat-card--warning .stat-card__dot {
  background: #f59e0b;
  box-shadow: 0 0 0 6px rgba(245, 158, 11, 0.16);
}
</style>
