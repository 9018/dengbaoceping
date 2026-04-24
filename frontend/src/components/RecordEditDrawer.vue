<template>
  <el-drawer v-model="visible" title="编辑测评记录" size="58%" class="record-edit-drawer">
    <div class="drawer-summary">
      <div class="summary-item">
        <div class="summary-item__label">当前状态</div>
        <div class="summary-item__value">{{ getStatusLabel('record', form.status) }}</div>
      </div>
      <div class="summary-item">
        <div class="summary-item__label">编辑重点</div>
        <div class="summary-item__value">final_content</div>
      </div>
    </div>

    <div class="drawer-layout">
      <el-card shadow="never">
        <template #header>
          <div>
            <div class="section-title">正文基线</div>
            <div class="section-subtitle">保留系统生成内容作为对照，避免复核过程丢失原始上下文。</div>
          </div>
        </template>
        <el-input v-model="form.record_content" type="textarea" :rows="14" />
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div>
            <div class="section-title">最终交付内容</div>
            <div class="section-subtitle">优先编辑 final_content，并同步维护状态、复核意见和复核人。</div>
          </div>
        </template>
        <el-form label-width="96px">
          <el-form-item label="最终正文">
            <el-input v-model="form.final_content" type="textarea" :rows="14" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status" class="w-full">
              <el-option v-for="status in recordStatusOptions" :key="status" :label="getStatusLabel('record', status)" :value="status" />
            </el-select>
          </el-form-item>
          <el-form-item label="复核意见">
            <el-input v-model="form.review_comment" />
          </el-form-item>
          <el-form-item label="复核人">
            <el-input v-model="form.reviewed_by" />
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <template #footer>
      <div class="drawer-footer">
        <el-button @click="emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" @click="emit('save', { ...form })">保存</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import type { EvaluationRecord } from '@/types/domain'
import { recordStatusOptions } from '@/utils/constants'
import { getStatusLabel } from '@/utils/status'

const props = defineProps<{
  modelValue: boolean
  record?: EvaluationRecord | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', value: Record<string, unknown>): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const form = reactive({
  record_content: '',
  final_content: '',
  status: 'reviewed',
  review_comment: '',
  reviewed_by: '',
})

watch(
  () => props.record,
  (record) => {
    form.record_content = record?.record_content || ''
    form.final_content = record?.final_content || record?.record_content || ''
    form.status = record?.status || 'reviewed'
    form.review_comment = record?.review_comment || ''
    form.reviewed_by = record?.reviewed_by || ''
  },
  { immediate: true },
)
</script>

<style scoped>
.record-edit-drawer :deep(.el-drawer__body) {
  padding-top: 10px;
}

.drawer-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.drawer-layout {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 16px;
}

.w-full {
  width: 100%;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 1280px) {
  .drawer-summary,
  .drawer-layout {
    grid-template-columns: 1fr;
  }
}
</style>
