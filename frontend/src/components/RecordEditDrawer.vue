<template>
  <el-drawer v-model="visible" title="编辑测评记录" size="62%" class="record-edit-drawer">
    <div class="drawer-summary">
      <div class="summary-item">
        <div class="summary-item__label">当前状态</div>
        <div class="summary-item__value">{{ getStatusLabel('record', form.status) }}</div>
      </div>
      <div class="summary-item">
        <div class="summary-item__label">模板定位</div>
        <div class="summary-item__value">{{ templatePosition }}</div>
      </div>
    </div>

    <div class="drawer-layout">
      <el-card shadow="never">
        <template #header>
          <div>
            <div class="section-title">模板 A-G 基线</div>
            <div class="section-subtitle">以项目模板原值为主线，对照当前正文、符合情况与缺失证据，避免复核时偏离模板结构。</div>
          </div>
        </template>
        <div class="template-grid">
          <div class="template-grid__item">
            <div class="panel-label">Sheet / 编号</div>
            <div class="muted-text">{{ templatePosition }}</div>
          </div>
          <div class="template-grid__item">
            <div class="panel-label">扩展标准</div>
            <div class="muted-text">{{ templateSnapshot.extension_standard || '—' }}</div>
          </div>
          <div class="template-grid__item">
            <div class="panel-label">控制点</div>
            <div class="muted-text">{{ templateSnapshot.control_point || '—' }}</div>
          </div>
          <div class="template-grid__item">
            <div class="panel-label">测评项</div>
            <div class="muted-text">{{ templateSnapshot.evaluation_item || props.record?.title || '—' }}</div>
          </div>
          <div class="template-grid__item">
            <div class="panel-label">模板符合情况</div>
            <div class="muted-text">{{ templateSnapshot.default_compliance || props.record?.conclusion || '—' }}</div>
          </div>
          <div class="template-grid__item">
            <div class="panel-label">分值</div>
            <div class="muted-text">{{ templateSnapshot.score_weight ?? '—' }}</div>
          </div>
        </div>
        <div class="template-block">
          <div class="panel-label">模板结果记录 D 列</div>
          <div class="template-block__content">{{ templateSnapshot.record_template || '—' }}</div>
        </div>
        <div class="template-block">
          <div class="panel-label">当前正文基线</div>
          <el-input v-model="form.record_content" type="textarea" :rows="8" />
        </div>
        <div v-if="missingEvidence.length || supportSummary.length || selectedReasonsSummary.length" class="match-summary">
          <div class="panel-label">辅助判断依据</div>
          <el-space wrap>
            <el-tag v-for="field in missingEvidence" :key="field" type="danger">缺失 {{ field }}</el-tag>
            <el-tag v-for="reason in selectedReasonsSummary" :key="reason" type="info">{{ reason }}</el-tag>
          </el-space>
          <div v-if="supportSummary.length" class="support-summary">
            {{ supportSummary.join('；') }}
          </div>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div>
            <div class="section-title">候选项与最终交付内容</div>
            <div class="section-subtitle">可切换模板候选重新生成，再同步维护最终正文、状态、复核意见和复核人。</div>
          </div>
        </template>
        <el-form label-width="110px">
          <el-form-item label="模板候选项">
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
        <el-button v-if="form.selected_item_code" type="warning" @click="emit('regenerate', { selected_item_code: form.selected_item_code })">按候选项重生成</el-button>
        <el-button type="primary" @click="emit('save', savePayload)">保存</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import type { EvaluationRecord, MatchCandidate, MatchReasons, RecordGenerationDetails, RecordTemplateSnapshot } from '@/types/domain'
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
const matchReasons = computed<MatchReasons>(() => {
  const reasons = props.record?.match_reasons
  return reasons && typeof reasons === 'object' ? (reasons as MatchReasons) : {}
})
const recordGeneration = computed<RecordGenerationDetails>(() => matchReasons.value.record_generation || {})
const templateSnapshot = computed<RecordTemplateSnapshot>(() => {
  const snapshot = props.record?.template_snapshot_json
  return snapshot && typeof snapshot === 'object' ? (snapshot as RecordTemplateSnapshot) : recordGeneration.value.template_snapshot || {}
})
const templatePosition = computed(() => [templateSnapshot.value.sheet_name || props.record?.sheet_name, templateSnapshot.value.item_no || props.record?.record_no || props.record?.item_code].filter(Boolean).join(' / ') || '未绑定模板')
const selectedReasonsSummary = computed(() => {
  const summary = matchReasons.value.summary
  return Array.isArray(summary) ? summary.slice(0, 4) : []
})
const missingEvidence = computed(() => {
  const missing = recordGeneration.value.missing_evidence
  return Array.isArray(missing) ? missing : []
})
const supportSummary = computed(() => {
  const summary = recordGeneration.value.evidence_summary
  return Array.isArray(summary) ? summary.slice(0, 3) : []
})
const savePayload = computed(() => ({
  record_content: form.record_content,
  final_content: form.final_content,
  status: form.status,
  review_comment: form.review_comment,
  reviewed_by: form.reviewed_by,
}))

function formatCandidateLabel(candidate: MatchCandidate) {
  const position = [candidate.sheet_name, candidate.record_no || candidate.item_no || candidate.item_code].filter(Boolean).join(' / ')
  return `${position || candidate.item_code || candidate.template_code || '未命名候选'} / ${candidate.score ?? '-'} 分`
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

.template-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.template-grid__item,
.template-block {
  padding: 12px;
  border: 1px solid var(--workspace-border-soft);
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.86);
}

.template-block {
  margin-top: 14px;
}

.template-block__content {
  margin-top: 8px;
  color: var(--workspace-text-secondary);
  line-height: 1.7;
  white-space: pre-wrap;
}

.match-summary {
  margin-top: 16px;
}

.support-summary {
  margin-top: 10px;
  color: var(--workspace-text-muted);
  line-height: 1.7;
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
  .drawer-layout,
  .template-grid {
    grid-template-columns: 1fr;
  }
}
</style>
