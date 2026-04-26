<template>
  <AppShell :project-id="projectId" title="测评记录页" subtitle="以项目结果记录参考模板为主驱动，围绕模板候选、缺失证据、人工确认和导出闭环推进记录复核。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">Template Driven Records</div>
            <div class="section-title">项目模板驱动的测评记录工作区</div>
            <div class="section-subtitle">优先展示模板 Sheet / 编号 / A-G 基线；指导书与历史记录退为辅助判断依据和写法参考。</div>
          </div>
          <el-space wrap>
            <el-button @click="loadData">刷新</el-button>
            <el-button type="primary" @click="generateDialogVisible = true">生成测评记录</el-button>
            <el-button type="success" @click="go(`/projects/${projectId}/exports`)">进入导出中心</el-button>
          </el-space>
        </div>
        <StatsCards :items="summaryCards" />
      </section>

      <section class="page-grid-3">
        <div class="soft-panel">
          <div class="panel-label">主模板状态</div>
          <div class="panel-value">{{ templateSummary ? '已导入项目模板' : '未导入项目模板' }}</div>
          <div class="panel-meta">{{ templateSummary ? `${templateSummary.item_count} 条模板行 / ${templateSummary.sheet_count} 个 Sheet` : '当前项目仍会回退到旧规则匹配链路' }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">模板来源文件</div>
          <div class="panel-value panel-value--path">{{ templateSummary?.source_file || '未上传 reference.xlsx' }}</div>
          <div class="panel-meta">{{ templateSummary?.sheet_names?.join('、') || '请先导入结果记录参考模板' }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">当前工作重点</div>
          <div class="panel-value">模板候选 → 人工确认 → 导出</div>
          <div class="panel-meta">D/E 作为正文与符合情况基线，F/G 保留模板原值。</div>
        </div>
      </section>

      <el-card>
        <template #header>
          <div class="section-header">
            <div class="section-title">记录生成与筛选</div>
            <div class="section-subtitle">在同一主表格里查看模板来源、Top 候选、缺失证据、最终正文和审批动作。</div>
          </div>
        </template>

        <div class="page-filter-bar">
          <el-form inline>
            <el-form-item label="模板 Sheet">
              <el-select v-model="sheetFilter" clearable placeholder="全部 Sheet" style="width: 220px">
                <el-option v-for="sheet in sheetOptions" :key="sheet" :label="sheet" :value="sheet" />
              </el-select>
            </el-form-item>
            <el-form-item label="设备筛选">
              <el-select v-model="deviceFilter" clearable placeholder="全部设备" style="width: 220px">
                <el-option v-for="device in deviceOptions" :key="device" :label="device" :value="device" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态筛选">
              <el-select v-model="statusFilter" clearable placeholder="全部状态" style="width: 180px">
                <el-option v-for="status in recordStatusOptions" :key="status" :label="getStatusLabel('record', status)" :value="status" />
              </el-select>
            </el-form-item>
            <el-form-item label="关键词">
              <el-input v-model="keywordFilter" clearable placeholder="搜索标题/模板编号/测评项/控制点" style="width: 280px" />
            </el-form-item>
          </el-form>
        </div>

        <el-table :data="filteredRecords" border>
          <el-table-column label="模板定位" min-width="240">
            <template #default="scope">
              <div class="cell-stack">
                <strong>{{ scope.row.sheet_name || '未绑定模板 Sheet' }}</strong>
                <span class="muted-text">编号 {{ scope.row.record_no || scope.row.item_code || '-' }} · 行 {{ scope.row.source_row_no || '-' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="测评项" min-width="220" />
          <el-table-column prop="device_name" label="设备" min-width="160" />
          <el-table-column label="匹配来源" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.match_source === 'project_template' ? 'success' : 'info'" effect="plain">
                {{ scope.row.match_source === 'project_template' ? '项目模板' : '旧规则' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="140">
            <template #default="scope">
              <AppStatusTag kind="record" :status="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="match_score" label="匹配得分" width="120" />
          <el-table-column prop="template_code" label="模板编码" width="170" />
          <el-table-column prop="item_code" label="测评项编码" width="170" />
          <el-table-column label="模板 A-G 摘要" min-width="280" show-overflow-tooltip>
            <template #default="scope">
              {{ getTemplateSummary(scope.row) }}
            </template>
          </el-table-column>
          <el-table-column label="Top 候选" min-width="280">
            <template #default="scope">
              <el-space wrap>
                <el-tag v-for="candidate in getTopCandidates(scope.row)" :key="`${candidate.item_code}-${candidate.template_code}-${candidate.sheet_name || 'sheet'}`" size="small">
                  {{ formatCandidateLabel(candidate) }}
                </el-tag>
              </el-space>
            </template>
          </el-table-column>
          <el-table-column label="缺失证据" min-width="240">
            <template #default="scope">
              <el-space wrap>
                <el-tag v-for="field in getMissingEvidence(scope.row)" :key="field" type="danger" size="small">{{ field }}</el-tag>
                <span v-if="!getMissingEvidence(scope.row).length">-</span>
              </el-space>
            </template>
          </el-table-column>
          <el-table-column label="辅助依据" min-width="260" show-overflow-tooltip>
            <template #default="scope">
              {{ getSupportSummary(scope.row) }}
            </template>
          </el-table-column>
          <el-table-column prop="final_content" label="最终正文" min-width="320" show-overflow-tooltip />
          <el-table-column label="操作" min-width="420" fixed="right">
            <template #default="scope">
              <el-space wrap>
                <el-button size="small" @click="openEditor(scope.row)">编辑</el-button>
                <el-tooltip :disabled="canMarkReviewed(scope.row.status)" :content="getMarkReviewedDisabledReason(scope.row.status)" placement="top">
                  <span class="action-wrapper">
                    <el-button size="small" type="primary" :disabled="!canMarkReviewed(scope.row.status)" @click="quickReview(scope.row.id, 'reviewed')">标记复核</el-button>
                  </span>
                </el-tooltip>
                <el-tooltip :disabled="canApprove(scope.row.status)" :content="getApproveDisabledReason(scope.row.status)" placement="top">
                  <span class="action-wrapper">
                    <el-button size="small" type="success" :disabled="!canApprove(scope.row.status)" @click="quickReview(scope.row.id, 'approved')">审批通过</el-button>
                  </span>
                </el-tooltip>
                <el-button size="small" @click="loadRecordAudit(scope.row.id)">审计</el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card v-if="auditLogs.length">
        <template #header>
          <div class="section-header">
            <div class="section-title">记录审计日志</div>
            <div class="section-subtitle">查看当前记录的复核轨迹和审批动作。</div>
          </div>
        </template>
        <el-timeline>
          <el-timeline-item v-for="log in auditLogs" :key="log.id" :timestamp="log.created_at">
            <div>{{ log.action }} / {{ log.reviewed_by || '未填写复核人' }}</div>
            <div class="muted-text">{{ log.review_comment || '无复核意见' }}</div>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <RecordEditDrawer v-model="drawerVisible" :record="editingRecord" @save="saveRecord" @regenerate="regenerateFromCandidate" />

      <el-dialog v-model="generateDialogVisible" title="生成测评记录" width="560px">
        <el-form label-width="120px">
          <el-form-item label="证据">
            <el-select v-model="generateEvidenceId" placeholder="请选择证据" class="w-full">
              <el-option v-for="item in evidences" :key="item.id" :label="item.title" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="设备类型覆盖">
            <el-input v-model="deviceTypeOverride" />
          </el-form-item>
          <el-form-item label="手动测评项">
            <el-input v-model="selectedItemCode" placeholder="可选，直接指定 item_code" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="generateDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="generateNewRecord">生成</el-button>
        </template>
      </el-dialog>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import AppStatusTag from '@/components/AppStatusTag.vue'
import RecordEditDrawer from '@/components/RecordEditDrawer.vue'
import StatsCards, { type StatsCardItem } from '@/components/StatsCards.vue'
import { listAssets } from '@/api/assets'
import { listEvidences } from '@/api/evidences'
import { getProjectReferenceTemplate } from '@/api/projects'
import { generateRecord, listRecordAuditLogs, listRecords, reviewRecord, updateRecord } from '@/api/records'
import { recordStatusOptions } from '@/utils/constants'
import { getStatusLabel } from '@/utils/status'
import type { Asset, AuditLog, EvaluationRecord, Evidence, MatchCandidate, MatchReasons, ProjectTemplateSummary, RecordTemplateSnapshot } from '@/types/domain'

interface RecordViewItem extends EvaluationRecord {
  device_name: string
  match_source: string | null
}

const props = defineProps<{ projectId: string }>()
const router = useRouter()
const records = ref<EvaluationRecord[]>([])
const evidences = ref<Evidence[]>([])
const assets = ref<Asset[]>([])
const auditLogs = ref<AuditLog[]>([])
const drawerVisible = ref(false)
const editingRecord = ref<EvaluationRecord | null>(null)
const generateDialogVisible = ref(false)
const generateEvidenceId = ref('')
const deviceTypeOverride = ref('')
const selectedItemCode = ref('')
const statusFilter = ref('')
const deviceFilter = ref('')
const sheetFilter = ref('')
const keywordFilter = ref('')
const templateSummary = ref<ProjectTemplateSummary | null>(null)

const recordRows = computed<RecordViewItem[]>(() => {
  const evidenceMap = new Map(evidences.value.map((item) => [item.id, item]))
  const assetMap = new Map(assets.value.map((item) => [item.id, item]))
  return records.value.map((record) => {
    const firstEvidence = record.evidence_ids.map((id) => evidenceMap.get(id)).find(Boolean)
    const asset = record.asset_id ? assetMap.get(record.asset_id) : undefined
    const reasons = getReasons(record)
    return {
      ...record,
      device_name: firstEvidence?.device || asset?.filename || '未绑定设备',
      match_source: reasons.match_source || null,
    }
  })
})

const deviceOptions = computed(() => Array.from(new Set(recordRows.value.map((item) => item.device_name).filter(Boolean))))
const sheetOptions = computed(() => Array.from(new Set(recordRows.value.map((item) => item.sheet_name).filter(Boolean))))

const summaryCards = computed<StatsCardItem[]>(() => [
  { label: '记录总数', value: records.value.length, tip: '当前项目全部测评记录', tone: 'primary' },
  { label: '模板驱动', value: records.value.filter((item) => getReasons(item).match_source === 'project_template').length, tip: '来自项目模板主链路', tone: 'success' },
  { label: '待复核', value: records.value.filter((item) => ['generated', 'generated_low_confidence'].includes(item.status)).length, tip: '需要人工确认模板候选与证据', tone: 'warning' },
  { label: '已审批/导出', value: records.value.filter((item) => ['approved', 'exported'].includes(item.status)).length, tip: '进入导出闭环', tone: 'default' },
])

const filteredRecords = computed(() => {
  const keyword = keywordFilter.value.trim().toLowerCase()
  return recordRows.value.filter((item) => {
    const snapshot = getTemplateSnapshot(item)
    const matchStatus = !statusFilter.value || item.status === statusFilter.value
    const matchDevice = !deviceFilter.value || item.device_name === deviceFilter.value
    const matchSheet = !sheetFilter.value || item.sheet_name === sheetFilter.value
    const matchKeyword =
      !keyword ||
      [item.title, item.template_code, item.item_code, item.record_no, snapshot.control_point, snapshot.evaluation_item, item.sheet_name]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(keyword))
    return matchStatus && matchDevice && matchSheet && matchKeyword
  })
})

async function loadData() {
  const [recordsResult, evidencesResult, assetsResult, templateResult] = await Promise.all([
    listRecords(props.projectId),
    listEvidences(props.projectId),
    listAssets(props.projectId),
    getProjectReferenceTemplate(props.projectId).catch(() => ({ data: null })),
  ])
  records.value = recordsResult.data
  evidences.value = evidencesResult.data
  assets.value = assetsResult.data
  templateSummary.value = templateResult.data
  if (!generateEvidenceId.value) {
    generateEvidenceId.value = evidences.value[0]?.id || ''
  }
}

function openEditor(record: EvaluationRecord) {
  editingRecord.value = record
  drawerVisible.value = true
}

function getReasons(record: EvaluationRecord): MatchReasons {
  const reasons = record.match_reasons
  return reasons && typeof reasons === 'object' ? (reasons as MatchReasons) : {}
}

function getTemplateSnapshot(record: EvaluationRecord): RecordTemplateSnapshot {
  const snapshot = record.template_snapshot_json
  return snapshot && typeof snapshot === 'object' ? (snapshot as RecordTemplateSnapshot) : {}
}

function getTopCandidates(record: EvaluationRecord): MatchCandidate[] {
  return Array.isArray(record.match_candidates) ? (record.match_candidates as MatchCandidate[]) : []
}

function getMissingEvidence(record: EvaluationRecord): string[] {
  const reasons = getReasons(record)
  const generation = reasons.record_generation
  return Array.isArray(generation?.missing_evidence) ? generation?.missing_evidence || [] : []
}

function getSupportSummary(record: EvaluationRecord) {
  const reasons = getReasons(record)
  const generation = reasons.record_generation
  const summary = Array.isArray(generation?.evidence_summary) ? generation?.evidence_summary || [] : []
  return summary.length ? summary.slice(0, 3).join('；') : '—'
}

function getTemplateSummary(record: EvaluationRecord) {
  const snapshot = getTemplateSnapshot(record)
  return [snapshot.extension_standard, snapshot.control_point, snapshot.evaluation_item, snapshot.default_compliance].filter(Boolean).join(' / ') || '—'
}

function formatCandidateLabel(candidate: MatchCandidate) {
  const position = [candidate.sheet_name, candidate.record_no || candidate.item_no || candidate.item_code].filter(Boolean).join(' / ')
  return `${position || candidate.item_code || candidate.template_code || '未命名候选'} · ${candidate.score ?? '-'} 分`
}

function canMarkReviewed(status: string) {
  return status === 'generated' || status === 'generated_low_confidence'
}

function getMarkReviewedDisabledReason(status: string) {
  return canMarkReviewed(status) ? '' : '仅待复核或低置信度记录可标记复核'
}

function canApprove(status: string) {
  return status === 'reviewed'
}

function getApproveDisabledReason(status: string) {
  return canApprove(status) ? '' : '仅已复核记录可审批通过'
}

async function saveRecord(payload: Record<string, unknown>) {
  if (!editingRecord.value) return
  await updateRecord(editingRecord.value.id, payload)
  ElMessage.success('记录更新成功')
  drawerVisible.value = false
  await loadData()
}

async function regenerateFromCandidate(payload: { selected_item_code?: string | null }) {
  if (!editingRecord.value) return
  await generateRecord(editingRecord.value.project_id, {
    evidence_id: editingRecord.value.evidence_ids[0],
    selected_item_code: payload.selected_item_code || null,
    force_regenerate: true,
  })
  ElMessage.success('已按候选项重生成记录')
  drawerVisible.value = false
  await loadData()
}

async function quickReview(recordId: string, status: string) {
  await reviewRecord(recordId, {
    status,
    review_comment: status === 'approved' ? '审批通过' : '标记已复核',
    reviewed_by: 'frontend-user',
  })
  ElMessage.success('记录复核成功')
  await loadData()
}

async function generateNewRecord() {
  if (!generateEvidenceId.value) {
    ElMessage.warning('请先选择证据')
    return
  }
  await generateRecord(props.projectId, {
    evidence_id: generateEvidenceId.value,
    device_type_override: deviceTypeOverride.value || null,
    selected_item_code: selectedItemCode.value || null,
    force_regenerate: false,
  })
  ElMessage.success('测评记录生成成功')
  generateDialogVisible.value = false
  await loadData()
}

async function loadRecordAudit(recordId: string) {
  const { data } = await listRecordAuditLogs(recordId)
  auditLogs.value = data
}

function go(path: string) {
  router.push(path)
}

onMounted(loadData)
</script>

<style scoped>
.cell-stack {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>
