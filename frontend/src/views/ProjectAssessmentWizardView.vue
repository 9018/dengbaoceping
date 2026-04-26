<template>
  <AppShell :project-id="projectId" title="项目测评向导" subtitle="围绕资产、测评表、证据、事实、模板行、草稿与写回形成项目内闭环。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">Project Assessment Wizard</div>
            <div class="section-title">项目内十步测评主流程</div>
            <div class="section-subtitle">从创建资产、生成项目测评表，到上传截图、OCR、识别事实、匹配测评项、生成 D/E 列草稿，再到人工确认写回。</div>
          </div>
          <el-space wrap>
            <el-button @click="loadWorkflowContext">刷新数据</el-button>
            <el-button @click="goEvidenceCenter">进入证据中心</el-button>
          </el-space>
        </div>
      </section>

      <section class="page-grid-4 overview-grid">
        <div class="soft-panel">
          <div class="panel-label">项目资产</div>
          <div class="panel-value">{{ assets.length }}</div>
          <div class="panel-meta">当前选择：{{ selectedAsset?.filename || '未选择' }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">项目测评表</div>
          <div class="panel-value">{{ workflowStore.projectTables.length }}</div>
          <div class="panel-meta">当前表：{{ workflowStore.currentTable?.name || '未生成' }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">项目证据</div>
          <div class="panel-value">{{ evidences.length }}</div>
          <div class="panel-meta">当前证据：{{ selectedEvidence?.title || '未选择' }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">当前测评项</div>
          <div class="panel-value">{{ workflowStore.currentItem?.item_code || '-' }}</div>
          <div class="panel-meta">状态：{{ workflowStore.currentItem?.status || 'pending' }}</div>
        </div>
      </section>

      <el-card>
        <template #header>
          <div class="section-header">
            <div class="section-title">步骤执行</div>
            <div class="section-subtitle">沿着项目主流程逐步推进，当前页面优先覆盖项目侧第 4-10 步。</div>
          </div>
        </template>

        <div class="wizard-stack">
          <WorkflowStepper :active="activeStep" :steps="steps" />

          <AssetCreateStep v-if="activeStep === 0" :assets="assets" @create="openCreateAsset" @refresh="loadAssetsOnly" />
          <ProjectTableGenerateStep
            v-else-if="activeStep === 1"
            :assets="assets"
            :tables="workflowStore.projectTables"
            :selected-asset-id="selectedAssetId"
            @select-asset="selectAsset"
            @generate="handleGenerateTable"
            @refresh="loadTablesOnly"
          />
          <EvidenceUploadOcrStep
            v-else-if="activeStep === 2"
            :evidences="evidences"
            :selected-evidence-id="selectedEvidenceId"
            :ocr-text="ocrText"
            @upload="evidenceDialogVisible = true"
            @ocr="handleRunOcr"
            @refresh="loadEvidenceOnly"
            @select-evidence="selectEvidence"
          />
          <EvidenceFactStep
            v-else-if="activeStep === 3"
            :selected-evidence-id="selectedEvidenceId"
            :result="workflowStore.extractedFacts"
            @extract="handleExtractFacts"
            @refresh="handleExtractFacts"
          />
          <TemplateRowMatchStep
            v-else-if="activeStep === 4"
            :selected-evidence-id="selectedEvidenceId"
            :result="workflowStore.matchedProjectItem"
            @match="handleMatchProjectItem"
            @refresh="handleMatchProjectItem"
            @select-candidate="selectProjectAssessmentItem"
          />
          <RecordDraftStep
            v-else-if="activeStep === 5"
            :item-id="workflowStore.currentProjectAssessmentItemId"
            :evidence-id="selectedEvidenceId"
            :draft="workflowStore.generatedDraft"
            @generate="handleGenerateDraft"
            @refresh="handleGenerateDraft"
          />
          <WriteBackConfirmStep
            v-else
            :item-id="workflowStore.currentProjectAssessmentItemId"
            :record-text="finalRecordText"
            :compliance-result="finalComplianceResult"
            :review-comment="reviewComment"
            :reviewed-by="reviewedBy"
            @confirm="handleConfirmItem"
            @refresh="reloadCurrentTableItems"
            @update:record-text="finalRecordText = $event"
            @update:compliance-result="finalComplianceResult = $event"
            @update:review-comment="reviewComment = $event"
            @update:reviewed-by="reviewedBy = $event"
          />

          <StepFooterActions
            v-if="activeStep < steps.length - 1"
            :show-previous="activeStep > 0"
            :disabled="nextDisabled"
            @previous="activeStep -= 1"
            @next="activeStep += 1"
          />
          <div v-else class="step-end-actions">
            <el-button @click="activeStep -= 1">上一步</el-button>
          </div>
        </div>
      </el-card>

      <AssetFormDialog v-model="assetDialogVisible" :asset="editingAsset" mode="create" @submit="createProjectAsset" />
      <EvidenceUploadDialog v-model="evidenceDialogVisible" @submit="submitEvidenceUpload" />
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import AssetFormDialog from '@/components/AssetFormDialog.vue'
import AssetCreateStep from '@/components/assessment/AssetCreateStep.vue'
import EvidenceFactStep from '@/components/assessment/EvidenceFactStep.vue'
import EvidenceUploadOcrStep from '@/components/assessment/EvidenceUploadOcrStep.vue'
import ProjectTableGenerateStep from '@/components/assessment/ProjectTableGenerateStep.vue'
import RecordDraftStep from '@/components/assessment/RecordDraftStep.vue'
import TemplateRowMatchStep from '@/components/assessment/TemplateRowMatchStep.vue'
import WriteBackConfirmStep from '@/components/assessment/WriteBackConfirmStep.vue'
import EvidenceUploadDialog from '@/components/EvidenceUploadDialog.vue'
import StepFooterActions from '@/components/workflow/StepFooterActions.vue'
import WorkflowStepper from '@/components/workflow/WorkflowStepper.vue'
import { createAsset, listAssets } from '@/api/assets'
import { getOcrResult, listEvidences, runOcr, uploadEvidence } from '@/api/evidences'
import {
  confirmProjectAssessmentItem,
  extractEvidenceFacts,
  generateProjectAssessmentDraft,
  generateProjectAssessmentTable,
  getProjectWorkflowStatus,
  listProjectAssessmentItems,
  listProjectAssessmentTables,
  matchProjectAssessmentItem,
} from '@/api/workflow'
import { useAppStore } from '@/stores/app'
import { useWorkflowStore } from '@/stores/workflow'
import type { Asset, Evidence } from '@/types/domain'

const props = defineProps<{ projectId: string; evidenceId?: string }>()

const router = useRouter()
const appStore = useAppStore()
const workflowStore = useWorkflowStore()

const activeStep = ref(0)
const assets = ref<Asset[]>([])
const evidences = ref<Evidence[]>([])
const ocrText = ref('')
const selectedAssetId = ref('')
const selectedEvidenceId = ref('')
const assetDialogVisible = ref(false)
const evidenceDialogVisible = ref(false)
const editingAsset = ref<Asset | null>(null)
const finalRecordText = ref('')
const finalComplianceResult = ref('')
const reviewComment = ref('')
const reviewedBy = ref('')

const steps = [
  { key: 'asset', title: '创建资产', summary: '维护项目测试对象' },
  { key: 'table', title: '生成测评表', summary: '按资产类型复制模板项' },
  { key: 'evidence', title: '上传并 OCR', summary: '准备项目截图证据' },
  { key: 'facts', title: '识别事实', summary: '提取页面类型和事实' },
  { key: 'match', title: '匹配测评项', summary: '映射到项目测评表行' },
  { key: 'draft', title: '生成草稿', summary: '生成 D/E 列建议' },
  { key: 'confirm', title: '人工确认', summary: '写回项目测评表' },
]

const selectedAsset = computed(() => assets.value.find((item) => item.id === selectedAssetId.value) || null)
const selectedEvidence = computed(() => evidences.value.find((item) => item.id === selectedEvidenceId.value) || null)
const nextDisabled = computed(() => {
  if (activeStep.value === 0) return assets.value.length === 0
  if (activeStep.value === 1) return !workflowStore.currentTableId || workflowStore.projectItems.length === 0
  if (activeStep.value === 2) return !selectedEvidenceId.value || selectedEvidence.value?.ocr_status !== 'completed'
  if (activeStep.value === 3) return !workflowStore.extractedFacts
  if (activeStep.value === 4) return !workflowStore.currentProjectAssessmentItemId
  if (activeStep.value === 5) return !workflowStore.generatedDraft
  return false
})

function selectAsset(value: string) {
  selectedAssetId.value = value
}

function selectEvidence(value: string) {
  selectedEvidenceId.value = value
}

function goEvidenceCenter() {
  router.push(`/projects/${props.projectId}/evidences`)
}

function syncConfirmFields() {
  const item = workflowStore.currentItem
  finalRecordText.value = item?.final_record_text || item?.draft_record_text || workflowStore.generatedDraft?.draft_record_text || ''
  finalComplianceResult.value = item?.final_compliance_result || item?.draft_compliance_result || workflowStore.generatedDraft?.draft_compliance_result || ''
  reviewComment.value = item?.review_comment || ''
  reviewedBy.value = item?.reviewed_by || ''
}

async function loadProjectStatus() {
  const { data } = await getProjectWorkflowStatus(props.projectId)
  workflowStore.setProjectStatus(data)
}

async function loadAssetsOnly() {
  const { data } = await listAssets(props.projectId)
  assets.value = data
  if (selectedAssetId.value && !assets.value.some((item) => item.id === selectedAssetId.value)) {
    selectedAssetId.value = ''
  }
  if (!selectedAssetId.value && assets.value.length) {
    selectedAssetId.value = assets.value[0].id
  }
}

async function loadTablesOnly() {
  const { data } = await listProjectAssessmentTables(props.projectId)
  workflowStore.setProjectTables(data)
  const currentTable = data.find((item) => item.id === workflowStore.currentTableId) || data.find((item) => item.asset_id === selectedAssetId.value) || null
  workflowStore.setCurrentTableId(currentTable?.id || '')
  if (workflowStore.currentTableId) {
    await loadProjectItems(workflowStore.currentTableId)
  } else {
    workflowStore.setProjectItems([])
    workflowStore.setCurrentProjectAssessmentItemId('')
  }
}

async function loadProjectItems(tableId: string) {
  const { data } = await listProjectAssessmentItems(tableId)
  workflowStore.setProjectItems(data)
  if (workflowStore.currentProjectAssessmentItemId && !data.some((item) => item.id === workflowStore.currentProjectAssessmentItemId)) {
    workflowStore.setCurrentProjectAssessmentItemId('')
  }
  syncConfirmFields()
}

async function loadEvidenceOnly() {
  const { data } = await listEvidences(props.projectId)
  evidences.value = data
  const preferredEvidenceId = selectedEvidenceId.value || workflowStore.currentEvidenceId || props.evidenceId
  if (preferredEvidenceId && evidences.value.some((item) => item.id === preferredEvidenceId)) {
    selectedEvidenceId.value = preferredEvidenceId
  } else if (selectedEvidenceId.value && evidences.value.some((item) => item.id === selectedEvidenceId.value)) {
    selectedEvidenceId.value = selectedEvidenceId.value
  } else {
    selectedEvidenceId.value = evidences.value[0]?.id || ''
  }
}

async function loadOcrText() {
  if (!selectedEvidenceId.value) {
    ocrText.value = ''
    return
  }
  try {
    const { data } = await getOcrResult(selectedEvidenceId.value)
    ocrText.value = data.full_text || ''
  } catch {
    ocrText.value = selectedEvidence.value?.text_content || ''
  }
}

async function loadWorkflowContext() {
  appStore.setLoading(true)
  try {
    await Promise.all([loadProjectStatus(), loadAssetsOnly(), loadEvidenceOnly()])
    await loadTablesOnly()
    await loadOcrText()
  } finally {
    appStore.setLoading(false)
  }
}

async function reloadCurrentTableItems() {
  if (!workflowStore.currentTableId) return
  await loadProjectItems(workflowStore.currentTableId)
}

function openCreateAsset() {
  editingAsset.value = {
    id: '',
    project_id: props.projectId,
    asset_kind: 'test_object',
    category: 'device',
    category_label: '设备资产',
    batch_no: null,
    filename: '',
    primary_ip: null,
    file_ext: null,
    mime_type: 'text/plain',
    relative_path: 'assets/device.txt',
    absolute_path: null,
    file_size: 0,
    file_sha256: null,
    file_mtime: null,
    source: 'manual',
    ingest_status: 'pending',
    created_at: '',
    updated_at: '',
  }
  assetDialogVisible.value = true
}

async function createProjectAsset(payload: Record<string, unknown>) {
  const { data, message } = await createAsset(props.projectId, payload as never)
  assetDialogVisible.value = false
  selectedAssetId.value = data.id
  ElMessage.success(message || '项目资产创建成功')
  await Promise.all([loadAssetsOnly(), loadProjectStatus()])
}

async function handleGenerateTable() {
  if (!selectedAssetId.value) {
    ElMessage.warning('请先选择资产')
    return
  }
  const { data, message } = await generateProjectAssessmentTable(props.projectId, selectedAssetId.value)
  workflowStore.setCurrentTableId(data.id)
  ElMessage.success(message || '项目测评表生成成功')
  await Promise.all([loadProjectStatus(), loadTablesOnly()])
}

async function submitEvidenceUpload(payload: Record<string, unknown>) {
  if (!payload.file) {
    ElMessage.warning('请选择证据文件')
    return
  }
  const { data, message } = await uploadEvidence(props.projectId, payload as never)
  evidenceDialogVisible.value = false
  selectedEvidenceId.value = data.id
  ElMessage.success(message || '证据上传成功')
  await loadEvidenceOnly()
  await loadOcrText()
}

async function handleRunOcr() {
  if (!selectedEvidenceId.value) {
    ElMessage.warning('请先选择证据')
    return
  }
  const { message } = await runOcr(selectedEvidenceId.value)
  ElMessage.success(message || 'OCR 执行成功')
  await loadEvidenceOnly()
  await loadOcrText()
}

async function handleExtractFacts() {
  if (!selectedEvidenceId.value) {
    ElMessage.warning('请先选择证据')
    return
  }
  const { data, message } = await extractEvidenceFacts(selectedEvidenceId.value)
  workflowStore.setExtractedFacts(data)
  ElMessage.success(message || '证据事实识别完成')
}

async function handleMatchProjectItem() {
  if (!selectedEvidenceId.value) {
    ElMessage.warning('请先选择证据')
    return
  }
  const { data, message } = await matchProjectAssessmentItem(selectedEvidenceId.value, props.projectId, selectedAssetId.value || undefined)
  workflowStore.setMatchedProjectItem(data)
  if (data.matched_project_assessment_item?.table_id && data.matched_project_assessment_item.table_id !== workflowStore.currentTableId) {
    workflowStore.setCurrentTableId(data.matched_project_assessment_item.table_id)
    await loadProjectItems(data.matched_project_assessment_item.table_id)
  }
  if (data.matched_project_assessment_item?.project_assessment_item_id) {
    workflowStore.setCurrentProjectAssessmentItemId(data.matched_project_assessment_item.project_assessment_item_id)
    syncConfirmFields()
  }
  ElMessage.success(message || '项目测评项匹配完成')
}

function selectProjectAssessmentItem(itemId: string) {
  workflowStore.setCurrentProjectAssessmentItemId(itemId)
  syncConfirmFields()
}

async function handleGenerateDraft() {
  if (!workflowStore.currentProjectAssessmentItemId || !selectedEvidenceId.value) {
    ElMessage.warning('请先完成测评项匹配')
    return
  }
  const { data, message } = await generateProjectAssessmentDraft(workflowStore.currentProjectAssessmentItemId, selectedEvidenceId.value)
  workflowStore.setGeneratedDraft(data)
  finalRecordText.value = data.draft_record_text || ''
  finalComplianceResult.value = data.draft_compliance_result || ''
  ElMessage.success(message || '测评记录草稿生成成功')
  await reloadCurrentTableItems()
}

async function handleConfirmItem() {
  if (!workflowStore.currentProjectAssessmentItemId) {
    ElMessage.warning('请先选择项目测评项')
    return
  }
  const { message } = await confirmProjectAssessmentItem(workflowStore.currentProjectAssessmentItemId, {
    final_record_text: finalRecordText.value || null,
    final_compliance_result: finalComplianceResult.value || null,
    review_comment: reviewComment.value || null,
    reviewed_by: reviewedBy.value || null,
  })
  ElMessage.success(message || '项目测评项确认成功')
  await reloadCurrentTableItems()
}

watch(selectedAssetId, async (value) => {
  if (!value) {
    workflowStore.setCurrentTableId('')
    workflowStore.setProjectItems([])
    workflowStore.setCurrentProjectAssessmentItemId('')
    return
  }
  const matchedTable = workflowStore.projectTables.find((item) => item.asset_id === value) || null
  workflowStore.setCurrentTableId(matchedTable?.id || '')
  if (matchedTable) {
    await loadProjectItems(matchedTable.id)
  } else {
    workflowStore.setProjectItems([])
    workflowStore.setCurrentProjectAssessmentItemId('')
  }
})

watch(selectedEvidenceId, async (value) => {
  workflowStore.setCurrentEvidenceId(value)
  workflowStore.setExtractedFacts(null)
  workflowStore.setMatchedProjectItem(null)
  workflowStore.setGeneratedDraft(null)
  await loadOcrText()
})

watch(
  () => workflowStore.currentProjectAssessmentItemId,
  () => {
    syncConfirmFields()
  },
)

onMounted(async () => {
  await loadWorkflowContext()
  if (props.evidenceId) {
    activeStep.value = 2
  }
})
</script>

<style scoped>
.overview-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.wizard-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.step-end-actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 1280px) {
  .overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
