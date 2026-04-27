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

      <section v-if="workflowStore.nextAction" class="page-section">
        <el-card>
          <div class="section-header">
            <div class="section-title">当前下一步动作</div>
            <div class="section-subtitle">{{ workflowStore.nextAction.message }}</div>
          </div>
          <div class="next-action-grid">
            <div class="soft-panel">
              <div class="panel-label">当前阶段</div>
              <div class="panel-value">{{ workflowStore.nextAction.stage }}</div>
              <div class="panel-meta">步骤：{{ workflowStore.nextAction.step_key }} / {{ workflowStore.nextAction.step_index + 1 }}</div>
            </div>
            <div class="soft-panel">
              <div class="panel-label">统计</div>
              <div class="panel-value">{{ workflowStore.nextAction.stats.confirmed_item_count }}/{{ workflowStore.nextAction.stats.item_count }}</div>
              <div class="panel-meta">已确认 / 总测评项</div>
            </div>
          </div>
        </el-card>
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
            :items="workflowStore.projectItems"
            :selected-asset-id="selectedAssetId"
            :current-table-id="workflowStore.currentTableId"
            :current-item-id="workflowStore.currentProjectAssessmentItemId"
            :conflict-message="tableConflictMessage"
            @select-asset="selectAsset"
            @generate="handleGenerateTable"
            @refresh="loadTablesOnly"
            @select-table="handleSelectTable"
            @rename-table="handleRenameTable"
            @regenerate-for-asset="handleRegenerateTable"
            @delete-table="handleDeleteTable"
            @select-item="selectProjectAssessmentItem"
            @edit-item="handleEditItem"
            @delete-item="handleDeleteItem"
          />
          <EvidenceUploadOcrStep
            v-else-if="activeStep === 2"
            :evidences="evidences"
            :selected-evidence-id="selectedEvidenceId"
            :ocr-text="ocrText"
            :ocr-health="ocrHealth"
            @upload="evidenceDialogVisible = true"
            @ocr="handleRunOcr"
            @refresh="loadEvidenceOnly"
            @select-evidence="selectEvidence"
            @save-manual-ocr="handleSaveManualOcr"
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
import type { AxiosError } from 'axios'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
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
import { getOcrHealth, getOcrResult, listEvidences, runOcr, saveManualOcrResult, uploadEvidence } from '@/api/evidences'
import {
  confirmProjectAssessmentItem,
  deleteProjectAssessmentItem,
  deleteProjectAssessmentTable,
  extractEvidenceFacts,
  generateProjectAssessmentDraft,
  generateProjectAssessmentTable,
  getProjectAssessmentNextAction,
  getProjectWorkflowStatus,
  listProjectAssessmentItems,
  listProjectAssessmentTables,
  matchProjectAssessmentItem,
  updateProjectAssessmentItem,
  updateProjectAssessmentTable,
} from '@/api/workflow'
import { useAppStore } from '@/stores/app'
import { useWorkflowStore } from '@/stores/workflow'
import type {
  ApiResponse,
  Asset,
  Evidence,
  OcrHealth,
  ProjectAssessmentItem,
  ProjectAssessmentTable,
  ProjectAssessmentTableConflictDetails,
} from '@/types/domain'

const props = defineProps<{ projectId: string; evidenceId?: string }>()

const router = useRouter()
const appStore = useAppStore()
const workflowStore = useWorkflowStore()

const activeStep = ref(0)
const assets = ref<Asset[]>([])
const evidences = ref<Evidence[]>([])
const ocrHealth = ref<OcrHealth | null>(null)
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
const tableConflictMessage = ref('')

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
const ocrReady = computed(() => {
  const evidence = selectedEvidence.value
  if (!evidence) return false
  return evidence.ocr_status === 'completed' || evidence.ocr_status === 'completed_with_warning' || Boolean(evidence.text_content?.trim())
})
const nextDisabled = computed(() => {
  if (activeStep.value === 0) return assets.value.length === 0
  if (activeStep.value === 1) return !workflowStore.currentTableId || workflowStore.projectItems.length === 0
  if (activeStep.value === 2) return !selectedEvidenceId.value || !ocrReady.value
  if (activeStep.value === 3) return !workflowStore.extractedFacts
  if (activeStep.value === 4) return !workflowStore.currentProjectAssessmentItemId
  if (activeStep.value === 5) return !workflowStore.generatedDraft
  return false
})

function selectAsset(value: string) {
  selectedAssetId.value = value
  tableConflictMessage.value = ''
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

function getActiveStepByKey(stepKey?: string | null) {
  const index = steps.findIndex((step) => step.key === stepKey)
  return index >= 0 ? index : 0
}

function applyNextActionSelection() {
  const nextAction = workflowStore.nextAction
  if (!nextAction) return
  if (nextAction.asset_id) {
    selectedAssetId.value = nextAction.asset_id
  }
  if (nextAction.evidence_id) {
    selectedEvidenceId.value = nextAction.evidence_id
  }
  if (nextAction.table_id) {
    workflowStore.setCurrentTableId(nextAction.table_id)
  }
  if (nextAction.item_id) {
    workflowStore.setCurrentProjectAssessmentItemId(nextAction.item_id)
  }
  if (nextAction.step_key && nextAction.step_key !== 'setup' && nextAction.step_key !== 'export') {
    activeStep.value = getActiveStepByKey(nextAction.step_key)
  }
}

function getApiError(error: unknown) {
  return (error as AxiosError<ApiResponse<unknown>>)?.response?.data?.error || null
}

function formatTableConflict(details?: Partial<ProjectAssessmentTableConflictDetails> | null) {
  if (!details) return '当前项目测评表存在受保护内容，需要显式确认。'
  return [
    `总条目 ${details.item_count ?? 0}`,
    `已确认 ${details.confirmed_item_count ?? 0}`,
    `人工编辑 ${details.edited_item_count ?? 0}`,
    `挂证据 ${details.linked_evidence_item_count ?? 0}`,
    `关联事实 ${details.linked_fact_count ?? 0}`,
  ].join('，')
}

async function loadProjectStatus() {
  const { data } = await getProjectWorkflowStatus(props.projectId)
  workflowStore.setProjectStatus(data)
}

async function loadNextAction() {
  const { data } = await getProjectAssessmentNextAction(props.projectId)
  workflowStore.setNextAction(data)
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
  workflowStore.setProjectTables(data.items)
  const currentTable = data.items.find((item) => item.id === workflowStore.currentTableId) || data.items.find((item) => item.asset_id === selectedAssetId.value) || null
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
  workflowStore.setProjectItems(data.items)
  if (workflowStore.currentProjectAssessmentItemId && !data.items.some((item) => item.id === workflowStore.currentProjectAssessmentItemId)) {
    workflowStore.setCurrentProjectAssessmentItemId('')
  }
  syncConfirmFields()
}

async function loadEvidenceOnly() {
  const { data } = await listEvidences(props.projectId)
  const health = await getOcrHealth()
  evidences.value = data
  ocrHealth.value = health.data
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
    await Promise.all([loadProjectStatus(), loadNextAction(), loadAssetsOnly(), loadEvidenceOnly()])
    applyNextActionSelection()
    await loadTablesOnly()
    if (workflowStore.currentTableId) {
      await loadProjectItems(workflowStore.currentTableId)
    }
    await loadOcrText()
    applyNextActionSelection()
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
  await Promise.all([loadAssetsOnly(), loadProjectStatus(), loadNextAction()])
  applyNextActionSelection()
}

async function generateTableForAsset(assetId: string, force = false) {
  const { data, message } = await generateProjectAssessmentTable(props.projectId, assetId, force)
  workflowStore.setCurrentTableId(data.id)
  selectedAssetId.value = assetId
  tableConflictMessage.value = ''
  ElMessage.success(message || (force ? '项目测评表已重新生成' : '项目测评表生成成功'))
  await Promise.all([loadProjectStatus(), loadNextAction(), loadTablesOnly()])
  applyNextActionSelection()
}

async function handleGenerateTable() {
  if (!selectedAssetId.value) {
    ElMessage.warning('请先选择资产')
    return
  }
  try {
    await generateTableForAsset(selectedAssetId.value)
  } catch (error) {
    const apiError = getApiError(error)
    if (!apiError) return
    if (apiError.code === 'PROJECT_ASSESSMENT_TABLE_REGENERATE_REQUIRES_FORCE') {
      const summary = formatTableConflict(apiError.details as Partial<ProjectAssessmentTableConflictDetails>)
      tableConflictMessage.value = `重新生成被保护：${summary}`
      try {
        await ElMessageBox.confirm(`当前资产的项目测评表已有处理痕迹：${summary}。是否确认强制重建？`, '重新生成确认', {
          type: 'warning',
          confirmButtonText: '确认重建',
          cancelButtonText: '取消',
        })
      } catch {
        return
      }
      await generateTableForAsset(selectedAssetId.value, true)
      return
    }
    if (apiError.code === 'PROJECT_ASSESSMENT_TABLE_ALREADY_EXISTS') {
      const summary = formatTableConflict(apiError.details as Partial<ProjectAssessmentTableConflictDetails>)
      tableConflictMessage.value = `当前资产已存在测评表：${summary}`
      return
    }
  }
}

async function handleSelectTable(tableId: string) {
  const table = workflowStore.projectTables.find((item) => item.id === tableId) || null
  if (!table) return
  workflowStore.setCurrentTableId(tableId)
  selectedAssetId.value = table.asset_id
  tableConflictMessage.value = ''
  await loadProjectItems(tableId)
}

async function handleRenameTable(table: ProjectAssessmentTable) {
  const { value } = await ElMessageBox.prompt('请输入新的项目测评表名称', '重命名测评表', {
    inputValue: table.name,
    inputPlaceholder: '项目测评表名称',
    confirmButtonText: '保存',
    cancelButtonText: '取消',
  })
  const name = value?.trim()
  if (!name || name === table.name) return
  const { message } = await updateProjectAssessmentTable(table.id, { name })
  ElMessage.success(message || '项目测评表重命名成功')
  await loadTablesOnly()
}

async function handleRegenerateTable(table: ProjectAssessmentTable) {
  selectedAssetId.value = table.asset_id
  await handleGenerateTable()
}

async function handleDeleteTable(table: ProjectAssessmentTable) {
  try {
    const { message } = await deleteProjectAssessmentTable(table.id)
    ElMessage.success(message || '项目测评表删除成功')
    if (workflowStore.currentTableId === table.id) {
      workflowStore.setCurrentTableId('')
      workflowStore.setProjectItems([])
      workflowStore.setCurrentProjectAssessmentItemId('')
    }
    tableConflictMessage.value = ''
    await Promise.all([loadProjectStatus(), loadNextAction(), loadTablesOnly()])
    applyNextActionSelection()
  } catch (error) {
    const apiError = getApiError(error)
    if (!apiError || apiError.code !== 'PROJECT_ASSESSMENT_TABLE_IN_USE') return
    const summary = formatTableConflict(apiError.details as Partial<ProjectAssessmentTableConflictDetails>)
    tableConflictMessage.value = `删除被保护：${summary}`
    try {
      await ElMessageBox.confirm(`当前测评表存在受保护内容：${summary}。是否确认强制删除？`, '删除确认', {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }
    const { message } = await deleteProjectAssessmentTable(table.id, true)
    ElMessage.success(message || '项目测评表已强制删除')
    if (workflowStore.currentTableId === table.id) {
      workflowStore.setCurrentTableId('')
      workflowStore.setProjectItems([])
      workflowStore.setCurrentProjectAssessmentItemId('')
    }
    tableConflictMessage.value = ''
    await Promise.all([loadProjectStatus(), loadNextAction(), loadTablesOnly()])
    applyNextActionSelection()
  }
}

async function handleEditItem(item: ProjectAssessmentItem) {
  const { value } = await ElMessageBox.prompt('请输入新的测评项文本', '编辑测评项', {
    inputValue: item.item_text || '',
    inputType: 'textarea',
    inputPlaceholder: '测评项文本',
    confirmButtonText: '保存',
    cancelButtonText: '取消',
  })
  const itemText = value?.trim()
  if (!itemText || itemText === (item.item_text || '')) return
  const { message } = await updateProjectAssessmentItem(item.id, { item_text: itemText })
  ElMessage.success(message || '项目测评项更新成功')
  await reloadCurrentTableItems()
}

async function handleDeleteItem(item: ProjectAssessmentItem) {
  try {
    const { message } = await deleteProjectAssessmentItem(item.id)
    ElMessage.success(message || '项目测评项删除成功')
  } catch (error) {
    const apiError = getApiError(error)
    if (!apiError || apiError.code !== 'PROJECT_ASSESSMENT_ITEM_IN_USE') return
    try {
      await ElMessageBox.confirm('当前测评项存在已确认、人工编辑或证据事实关联，是否确认强制删除？', '删除确认', {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }
    const { message } = await deleteProjectAssessmentItem(item.id, true)
    ElMessage.success(message || '项目测评项已强制删除')
  }
  if (workflowStore.currentProjectAssessmentItemId === item.id) {
    workflowStore.setCurrentProjectAssessmentItemId('')
  }
  await Promise.all([reloadCurrentTableItems(), loadProjectStatus(), loadNextAction(), loadTablesOnly()])
  applyNextActionSelection()
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
  await loadProjectStatus()
  await loadNextAction()
  applyNextActionSelection()
}

async function handleRunOcr(force = false) {
  if (!selectedEvidenceId.value) {
    ElMessage.warning('请先选择证据')
    return
  }
  const { data, message } = await runOcr(selectedEvidenceId.value, undefined, force)
  const ocrStatus = data.ocr_status
  if (ocrStatus === 'completed_with_warning') {
    ElMessage.warning(data.ocr_error_message || message || 'OCR 已完成，但存在告警')
  } else if (ocrStatus === 'failed') {
    ElMessage.error(data.ocr_error_message || message || 'OCR 执行失败')
  } else {
    ElMessage.success(message || 'OCR 执行成功')
  }
  await loadEvidenceOnly()
  await loadOcrText()
  await loadProjectStatus()
  await loadNextAction()
  applyNextActionSelection()
}

async function handleSaveManualOcr(text: string) {
  if (!selectedEvidenceId.value) {
    ElMessage.warning('请先选择证据')
    return
  }
  await saveManualOcrResult(selectedEvidenceId.value, text)
  ElMessage.success('手工 OCR 保存成功')
  await loadEvidenceOnly()
  await loadOcrText()
  await loadProjectStatus()
  await loadNextAction()
  applyNextActionSelection()
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
  await loadProjectStatus()
  await loadNextAction()
  applyNextActionSelection()
  if (workflowStore.nextAction?.stage === 'completed') {
    ElMessage.success('当前项目测评流程已完成，可进入导出中心')
  }
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
