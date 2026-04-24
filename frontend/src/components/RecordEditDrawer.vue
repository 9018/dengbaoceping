<template>
  <el-drawer v-model="visible" title="编辑测评记录" size="62%" class="record-edit-drawer">
    <div class="drawer-summary">
      <div class="summary-item">
        <div class="summary-item__label">当前状态</div>
        <div class="summary-item__value">{{ getStatusLabel('record', form.status) }}</div>
      </div>
      <div class="summary-item">
        <div class="summary-item__label">编辑重点</div>
        <div class="summary-item__value">final_content / 候选项</div>
      </div>
    </div>

    <div class="drawer-layout">
      <el-card shadow="never">
        <template #header>
          <div>
            <div class="section-title">正文基线</div>
            <div class="section-subtitle">保留系统生成内容与匹配摘要作为对照，避免复核过程丢失上下文。</div>
          </div>
        </template>
        <el-input v-model="form.record_content" type="textarea" :rows="12" />
        <div class="match-summary" v-if="selectedReasonsSummary.length || selectedMissingFields.length">
          <div class="panel-label">匹配摘要</div>
          <el-space wrap>
            <el-tag v-for="field in selectedMissingFields" :key="field" type="danger">缺失 {{ field }}</el-tag>
            <el-tag v-for="reason in selectedReasonsSummary" :key="reason" type="info">{{ reason }}</el-tag>
          </el-space>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div>
            <div class="section-title">候选项与最终交付内容</div>
            <div class="section-subtitle">可切换候选测评项重新生成，再同步维护状态、复核意见和复核人。</div>
          </div>
        </template>
        <el-form label-width="110px">
          <el-form-item label="候选测评项">
            <el-select v-model="form.selected_item_code" clearable class="w-full" placeholder="使用当前最佳匹配">
              <el-option
                v-for="candidate in candidateOptions"
                :key="candidate.item_code || candidate.template_code || 'candidate'"
                :label="formatCandidateLabel(candidate)"
                :value="candidate.item_code || undefined"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="最终正文">
            <el-input v-model="form.final_content" type="textarea" :rows="12" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status" class="w-full">
              <el-option v-for="status in recordStatusOptions" :key="status" :label="getStatusLabel('record', status)
" :value="status" />
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
        <el-button v-if="form.selected_item_code" type="warning" @click="emit('regenerate', { selected_item_code: form.selected_item_code })">按候选项重生成</el-button>
        <el-button type="primary" @click="emit('save', savePayload)">保存</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import type { EvaluationRecord, MatchCandidate } from '@/types/domain'
import { recordStatusOptions } from '@/utils/constants'
import { getStatusLabel } from '@/utils/status'

const props = defineProps<{
  modelValue: boolean
  record?: EvaluationRecord | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', value: Record<string, unknown>): void
  (e: 'regenerate', value: { selected_item_code?: string | null }): void
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
  selected_item_code: '',
})

const candidateOptions = computed<MatchCandidate[]>(() => Array.isArray(props.record?.match_candidates) ? props.record?.match_candidates || [] : [])
const selectedReasonsSummary = computed(() => {
  const reasons = props.record?.match_reasons
  if (!reasons || typeof reasons !== 'object') return []
  const summary = (reasons as { summary?: string[] }).summary
  return Array.isArray(summary) ? summary.slice(0, 4) : []
})
const selectedMissingFields = computed(() => {
  const reasons = props.record?.match_reasons
  if (!reasons || typeof reasons !== 'object') return []
  const missing = (reasons as { missing_required_fields?: string[] }).missing_required_fields
  return Array.isArray(missing) ? missing : []
})
const savePayload = computed(() => ({
  record_content: form.record_content,
  final_content: form.final_content,
  status: form.status,
  review_comment: form.review_comment,
  reviewed_by: form.reviewed_by,
}))

function formatCandidateLabel(candidate: MatchCandidate) {
  return `${candidate.item_code || candidate.template_code || '未命名候选'} / ${candidate.score ?? '-'} 分`
}

watch(
  () => props.record,
  (record) => {
    form.record_content = record?.record_content || ''
    form.final_content = record?.final_content || record?.record_content || ''
    form.status = record?.status || 'reviewed'
    form.review_comment = record?.review_comment || ''
    form.reviewed_by = record?.reviewed_by || ''
    form.selected_item_code = ''
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
  grid-template-columns: 1fr 1.25fr;
  gap: 16px;
}

.match-summary {
  margin-top: 16px;
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
