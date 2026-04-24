<template>
  <div>
    <el-table :data="fields" border>
      <el-table-column prop="field_group" label="字段组" min-width="120" />
      <el-table-column prop="field_name" label="字段名" min-width="140" />
      <el-table-column prop="raw_value" label="原始值" min-width="160" />
      <el-table-column label="修正值" min-width="180">
        <template #default="scope">
          <el-input v-model="editable[scope.row.id].corrected_value" />
        </template>
      </el-table-column>
      <el-table-column label="状态" min-width="180">
        <template #default="scope">
          <div class="status-editor">
            <el-tag :type="getFieldStatusTagType(scope.row.status)" effect="light">{{ getFieldStatusLabel(scope.row.status) }}</el-tag>
            <el-select v-model="editable[scope.row.id].status">
              <el-option v-for="status in fieldStatusOptions" :key="status" :label="getFieldStatusLabel(status)" :value="status" />
            </el-select>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="复核意见" min-width="180">
        <template #default="scope">
          <el-input v-model="editable[scope.row.id].review_comment" />
        </template>
      </el-table-column>
      <el-table-column label="复核人" min-width="120">
        <template #default="scope">
          <el-input v-model="editable[scope.row.id].reviewed_by" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="scope">
          <el-space>
            <el-button size="small" type="primary" @click="emit('update', scope.row.id, editable[scope.row.id])">保存</el-button>
            <el-button size="small" @click="emit('review', scope.row.id, editable[scope.row.id])">复核</el-button>
            <el-button size="small" @click="emit('audit', scope.row.id)">审计</el-button>
          </el-space>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import type { ExtractedField } from '@/types/domain'
import { fieldStatusOptions } from '@/utils/constants'

const props = defineProps<{ fields: ExtractedField[] }>()
const emit = defineEmits<{
  (e: 'update', fieldId: string, payload: Record<string, unknown>): void
  (e: 'review', fieldId: string, payload: Record<string, unknown>): void
  (e: 'audit', fieldId: string): void
}>()

const editable = reactive<Record<string, Record<string, unknown>>>({})

const fieldStatusLabelMap: Record<string, string> = {
  missing: '缺失',
  extracted: '已抽取',
  reviewed: '已复核',
  corrected: '已修正',
  rejected: '已驳回',
}

function getFieldStatusLabel(status: string | null | undefined) {
  if (!status) return '待处理'
  return fieldStatusLabelMap[status] || status
}

function getFieldStatusTagType(status: string | null | undefined) {
  if (!status) return 'info'
  if (status === 'reviewed') return 'success'
  if (status === 'corrected') return 'warning'
  if (status === 'rejected') return 'danger'
  if (status === 'missing') return 'info'
  return 'primary'
}

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
.status-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
