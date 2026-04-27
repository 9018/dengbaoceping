<template>
  <AppShell :project-id="projectId" title="证据中心页" subtitle="围绕证据采集、OCR 与进入证据处理向导构建清晰主流程。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">Evidence Pipeline</div>
            <div class="section-title">证据流水线中心</div>
            <div class="section-subtitle">统一查看证据元信息、识别状态和下一步动作，把主流程收束到证据处理向导。</div>
          </div>
          <el-space wrap>
            <el-button @click="loadEvidences">刷新</el-button>
            <el-button type="primary" @click="dialogVisible = true">上传证据</el-button>
          </el-space>
        </div>
        <StatsCards :items="summaryCards" />
      </section>

      <el-card>
        <template #header>
          <div class="section-header">
            <div class="section-title">证据流水线</div>
            <div class="section-subtitle">按关键词筛选证据，并从当前状态直接进入向导处理、查看结果或执行备用 OCR。</div>
          </div>
        </template>

        <div class="page-filter-bar">
          <el-form inline>
            <el-form-item label="关键词">
              <el-input v-model="keyword" clearable placeholder="搜索证据标题、设备、摘要" style="width: 280px" />
            </el-form-item>
          </el-form>
        </div>

        <el-table :data="filteredEvidences" border>
          <el-table-column prop="title" label="证据标题" min-width="200" />
          <el-table-column prop="device" label="关联设备" min-width="140" />
          <el-table-column prop="evidence_type" label="类型" width="120" />
          <el-table-column label="OCR 状态" width="130">
            <template #default="scope">
              <AppStatusTag kind="ocr" :status="scope.row.ocr_status" />
            </template>
          </el-table-column>
          <el-table-column label="OCR Provider" width="140">
            <template #default="scope">
              {{ scope.row.ocr_provider || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="下一步动作" min-width="180">
            <template #default="scope">
              {{ getPipelineHint(scope.row) }}
            </template>
          </el-table-column>
          <el-table-column prop="summary" label="摘要" min-width="240" show-overflow-tooltip />
          <el-table-column label="操作" min-width="420" fixed="right">
            <template #default="scope">
              <el-space wrap>
                <el-button size="small" @click="runOcrFor(scope.row.id)">执行 OCR</el-button>
                <el-button size="small" :type="getWizardEntryType(scope.row)" @click="goWizard(scope.row.id)">
                  {{ getWizardEntryLabel(scope.row) }}
                </el-button>
                <el-popconfirm title="确认删除该证据？" @confirm="removeEvidence(scope.row.id)">
                  <template #reference>
                    <el-button size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <EvidenceUploadDialog v-model="dialogVisible" @submit="submitUpload" />
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import AppStatusTag from '@/components/AppStatusTag.vue'
import EvidenceUploadDialog from '@/components/EvidenceUploadDialog.vue'
import StatsCards, { type StatsCardItem } from '@/components/StatsCards.vue'
import { deleteEvidence, listEvidences, runOcr, uploadEvidence } from '@/api/evidences'
import { listRecords } from '@/api/records'
import type { Evidence, EvaluationRecord } from '@/types/domain'

const props = defineProps<{ projectId: string }>()
const router = useRouter()
const evidences = ref<Evidence[]>([])
const records = ref<EvaluationRecord[]>([])
const dialogVisible = ref(false)
const keyword = ref('')

const summaryCards = computed<StatsCardItem[]>(() => [
  { label: '证据总数', value: evidences.value.length, tip: '项目内全部证据', tone: 'primary' },
  { label: '待 OCR', value: evidences.value.filter((item) => !['completed', 'completed_with_warning'].includes(item.ocr_status || '') && !item.text_content?.trim()).length, tip: '优先推进识别', tone: 'warning' },
  { label: '已完成 OCR', value: evidences.value.filter((item) => ['completed', 'completed_with_warning'].includes(item.ocr_status || '') || Boolean(item.text_content?.trim())).length, tip: '可进入向导分析', tone: 'success' },
  { label: '已生成记录', value: records.value.length, tip: '可进入结果复核', tone: 'default' },
])

const generatedEvidenceIds = computed(() => new Set(records.value.flatMap((item) => item.evidence_ids)))

const filteredEvidences = computed(() => {
  const search = keyword.value.trim().toLowerCase()
  return evidences.value.filter((item) => {
    if (!search) return true
    return [item.title, item.device, item.summary]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(search))
  })
})

async function loadEvidences() {
  const [evidenceResult, recordsResult] = await Promise.all([listEvidences(props.projectId), listRecords(props.projectId)])
  evidences.value = evidenceResult.data
  records.value = recordsResult.data
}

function hasGeneratedRecord(evidence: Evidence) {
  return generatedEvidenceIds.value.has(evidence.id)
}

function isEvidenceOcrReady(evidence: Evidence) {
  return ['completed', 'completed_with_warning'].includes(evidence.ocr_status || '') || Boolean(evidence.text_content?.trim())
}

function getWizardEntryType(evidence: Evidence) {
  return isEvidenceOcrReady(evidence) || hasGeneratedRecord(evidence) ? 'success' : 'primary'
}

function getWizardEntryLabel(evidence: Evidence) {
  if (hasGeneratedRecord(evidence)) return '查看结果'
  if (isEvidenceOcrReady(evidence)) return '继续向导分析'
  return '进入向导处理'
}

function getPipelineHint(evidence: Evidence) {
  if (hasGeneratedRecord(evidence)) return '查看结果'
  if (isEvidenceOcrReady(evidence)) return '继续向导分析'
  return '进入向导处理'
}

async function submitUpload(payload: Record<string, unknown>) {
  if (!payload.file) {
    ElMessage.warning('请选择证据文件')
    return
  }
  await uploadEvidence(props.projectId, payload as never)
  ElMessage.success('证据上传成功')
  dialogVisible.value = false
  await loadEvidences()
}

async function runOcrFor(evidenceId: string) {
  await runOcr(evidenceId)
  ElMessage.success('OCR 执行成功')
  await loadEvidences()
}

function goWizard(evidenceId: string) {
  router.push(`/projects/${props.projectId}/assessment-wizard?evidenceId=${evidenceId}`)
}

async function removeEvidence(evidenceId: string) {
  await deleteEvidence(evidenceId)
  ElMessage.success('证据已删除')
  await loadEvidences()
}

onMounted(loadEvidences)
</script>
