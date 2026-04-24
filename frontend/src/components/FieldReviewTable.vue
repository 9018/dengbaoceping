<template>
  <div class="field-review-panel">
    <div v-for="group in groupedFields" :key="group.name" class="field-group">
      <div class="field-group__header">
        <div>
          <div class="field-group__title">{{ group.name }}</div>
          <div class="field-group__subtitle">共 {{ group.items.length }} 个字段，支持保存、复核与查看审计。</div>
        </div>
      </div>

      <div class="field-grid">
        <el-card v-for="field in group.items" :key="field.id" class="field-card" shadow="never">
          <div class="field-card__top">
            <div>
              <div class="field-card__name">{{ field.field_name }}</div>
              <div class="field-card__meta">规则ID：{{ field.rule_id || '未绑定' }}</div>
            </div>
            <AppStatusTag kind="field" :status="editable[field.id]?.status as string" />
          </div>

          <div class="field-card__section">
            <div class="field-card__label">原始值</div>
            <div class="field-card__raw">{{ field.raw_value || '未抽取到原始值' }}</div>
          </div>

          <div class="field-card__section">
            <div class="field-card__label">修正值</div>
            <el-input v-model="editable[field.id].corrected_value" type="textarea" :rows="2" />
          </div>

          <div class="field-card__section field-card__section--inline">
            <div>
              <div class="field-card__label">状态</div>
              <el-select v-model="editable[field.id].status" class="field-card__select">
                <el-option v-for="status in fieldStatusOptions" :key="status" :label="getStatusLabel('field', status)" :value="status" />
              </el-select>
            </div>
            <div>
              <div class="field-card__label">复核人</div>
              <el-input v-model="editable[field.id].reviewed_by" />
            </div>
          </div>

          <div class="field-card__section">
            <div class="field-card__label">复核意见</div>
            <el-input v-model="editable[field.id].review_comment" type="textarea" :rows="2" />
          </div>

          <div class="field-card__actions">
            <el-button size="small" type="primary" @click="emit('update', field.id, editable[field.id])">保存</el-button>
            <el-button size="small" @click="emit('review', field.id, editable[field.id])">复核</el-button>
            <el-button size="small" @click="emit('audit', field.id)">审计</el-button>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import AppStatusTag from '@/components/AppStatusTag.vue'
import type { ExtractedField } from '@/types/domain'
import { fieldStatusOptions } from '@/utils/constants'
import { getStatusLabel } from '@/utils/status'

const props = defineProps<{ fields: ExtractedField[] }>()
const emit = defineEmits<{
  (e: 'update', fieldId: string, payload: Record<string, unknown>): void
  (e: 'review', fieldId: string, payload: Record<string, unknown>): void
  (e: 'audit', fieldId: string): void
}>()

const editable = reactive<Record<string, Record<string, unknown>>>({})

const groupedFields = computed(() => {
  const groups = new Map<string, ExtractedField[]>()
  props.fields.forEach((field) => {
    const key = field.field_group || '未分组'
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)?.push(field)
  })
  return Array.from(groups.entries()).map(([name, items]) => ({ name, items }))
})

watch(
  () => props.fields,
  (items) => {
    items.forEach((item) => {
      editable[item.id] = {
        corrected_value: item.corrected_value,
        status: item.status || 'reviewed',
        review_comment: item.review_comment,
        reviewed_by: item.reviewed_by,
      }
    })
  },
  { immediate: true },
)
</script>

<style scoped>
.field-review-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-group__title {
  font-size: 16px;
  font-weight: 700;
  color: #111827;
  text-transform: capitalize;
}

.field-group__subtitle {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}

.field-card {
  border-radius: 16px;
  border: 1px solid #e5eaf3;
}

.field-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.field-card__name {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.field-card__meta {
  margin-top: 4px;
  font-size: 12px;
  color: #8a94a6;
}

.field-card__section {
  margin-top: 14px;
}

.field-card__section--inline {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.field-card__label {
  margin-bottom: 8px;
  font-size: 12px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.field-card__raw {
  min-height: 44px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e5eaf3;
  line-height: 1.6;
  color: #1f2937;
}

.field-card__select {
  width: 100%;
}

.field-card__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
</style>
