<template>
  <el-card shadow="hover" class="stat-card" :class="[`stat-card--${tone}`, { 'stat-card--clickable': clickable }]" @click="handleClick">
    <div class="stat-card__inner">
      <div class="stat-card__head">
        <div>
          <div class="stat-card__label">{{ label }}</div>
          <div v-if="tip" class="stat-card__tip">{{ tip }}</div>
        </div>
        <div class="stat-card__signal">
          <div class="stat-card__signal-core" />
        </div>
      </div>
      <div class="stat-card__value">{{ value }}</div>
      <div class="stat-card__footer">
        <span>工作台指标</span>
        <span v-if="clickable">点击查看</span>
      </div>
    </div>
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
  overflow: hidden;
  border: 1px solid var(--workspace-border);
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(245, 248, 252, 0.98));
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
}

.stat-card--clickable {
  cursor: pointer;
}

.stat-card__inner {
  position: relative;
}

.stat-card__inner::after {
  content: '';
  position: absolute;
  inset: auto -30px -46px auto;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: rgba(15, 23, 42, 0.04);
}

.stat-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.stat-card__label {
  color: var(--workspace-text-secondary);
  font-size: 13px;
  font-weight: 700;
}

.stat-card__tip {
  margin-top: 8px;
  color: var(--workspace-text-muted);
  font-size: 12px;
  line-height: 1.6;
}

.stat-card__value {
  position: relative;
  z-index: 1;
  margin-top: 24px;
  font-size: 34px;
  line-height: 1;
  font-weight: 800;
  color: var(--workspace-text);
}

.stat-card__footer {
  position: relative;
  z-index: 1;
  margin-top: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--workspace-text-muted);
  font-size: 12px;
}

.stat-card__signal {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(148, 163, 184, 0.12);
}

.stat-card__signal-core {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #94a3b8;
  box-shadow: 0 0 0 6px rgba(148, 163, 184, 0.16);
}

.stat-card--primary .stat-card__signal {
  background: rgba(37, 99, 235, 0.12);
}

.stat-card--primary .stat-card__signal-core {
  background: #2563eb;
  box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.14);
}

.stat-card--success .stat-card__signal {
  background: rgba(5, 150, 105, 0.12);
}

.stat-card--success .stat-card__signal-core {
  background: #059669;
  box-shadow: 0 0 0 6px rgba(5, 150, 105, 0.14);
}

.stat-card--warning .stat-card__signal {
  background: rgba(217, 119, 6, 0.12);
}

.stat-card--warning .stat-card__signal-core {
  background: #d97706;
  box-shadow: 0 0 0 6px rgba(217, 119, 6, 0.14);
}
</style>
