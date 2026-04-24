<template>
  <AppShell :project-id="projectId" title="证据中心页" subtitle="围绕证据采集、OCR、字段抽取与进入复核构建专业工作流。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">Evidence Pipeline</div>
            <div class="section-title">证据流水线中心</div>
            <div class="section-subtitle">统一查看证据元信息、识别状态、抽取入口和下一步动作，避免工作流断点。</div>
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
            <div class="section-subtitle">按 OCR 样例、抽取模板与关键词快速筛选证据，并从当前状态直接进入下一步动作。</div>
          </div>
        </template>

        <div class="page-filter-bar">
          <el-form inline>
            <el-form-item label="OCR 样例">
              <el-select v-model="selectedSampleId" style="width: 240px">
                <el-option v-for="sample in ocrSampleOptions" :key="sample" :label="sample" :value="sample" />
              </el-select>
            </el-form-item>
            <el-form-item label="抽取模板">
              <el-select v-model="selectedTemplateCode" style="width: 240px">
                <el-option v-for="code in templateCodeOptions" :key="code" :label="code" :value="code" />
              </el-select>
            </el-form-item>
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
          <el-table-column label="操作" min-width="520" fixed="right">
            <template #default="scope">
              <el-space wrap>
                <el-button size="small" @click="runOcrFor(scope.row.id)">执行 OCR</el-button>
                <el-tooltip :disabled="canExtractFields(scope.row)" content="请先执行 OCR，再进行字段抽取" placement="top">
                  <span class="action-wrapper">
                    <el-button size="small" :disabled="!canExtractFields(scope.row)" @click="extractFor(scope.row.id)">字段抽取</el-button>
                  </span>
                </el-tooltip>
                <el-button size="small" :type="getReviewEntryType(scope.row)" @click="goReview(scope.row.id)">
                  {{ getReviewEntryLabel(scope.row) }}
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
import { deleteEvidence, extractFields, listEvidences, runOcr, uploadEvidence } from '@/api/evidences'
import { ocrSampleOptions, templateCodeOptions } from '@/utils/constants'
import type { Evidence } from '@/types/domain'

const props = defineProps<{ projectId: string }>()
const router = useRouter()
const evidences = ref<Evidence[]>([])
const dialogVisible = ref(false)
const selectedSampleId = ref('firewall_basic')
const selectedTemplateCode = ref('security_device_basic')
const keyword = ref('')

const summaryCards = computed<StatsCardItem[]>(() => [
  { label: '证据总数', value: evidences.value.length, tip: '项目内全部证据', tone: 'primary' },
  { label: '待 OCR', value: evidences.value.filter((item) => item.ocr_status !== 'completed').length, tip: '优先推进识别', tone: 'warning' },
  { label: '已完成 OCR', value: evidences.value.filter((item) => item.ocr_status === 'completed').length, tip: '可进入抽取与复核', tone: 'success' },
  { label: '待抽取', value: evidences.value.filter((item) => item.ocr_status === 'completed' && item.text_content).length, tip: '满足抽取前置条件', tone: 'default' },
])

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
  const { data } = await listEvidences(props.projectId)
  evidences.value = data
}

function canExtractFields(evidence: Evidence) {
  return evidence.ocr_status === 'completed' && Boolean(evidence.text_content)
}

function getReviewEntryType(evidence: Evidence) {
  return canExtractFields(evidence) ? 'success' : 'primary'
}

function getReviewEntryLabel(evidence: Evidence) {
  return canExtractFields(evidence) ? '进入识别复核' : '识别复核'
}

function getPipelineHint(evidence: Evidence) {
  if (evidence.ocr_status !== 'completed') return '先执行 OCR，补齐识别结果。'
  if (!evidence.text_content) return '当前 OCR 文本为空，需确认识别结果。'
  return '可以继续字段抽取并进入识别复核。'
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
  await runOcr(evidenceId, selectedSampleId.value)
  ElMessage.success('OCR 执行成功')
  await loadEvidences()
}

async function extractFor(evidenceId: string) {
  await extractFields(evidenceId, selectedTemplateCode.value)
  ElMessage.success('字段抽取完成')
  router.push(`/projects/${props.projectId}/review?evidenceId=${evidenceId}`)
}

function goReview(evidenceId: string) {
  router.push(`/projects/${props.projectId}/review?evidenceId=${evidenceId}`)
}

async function removeEvidence(evidenceId: string) {
  await deleteEvidence(evidenceId)
  ElMessage.success('证据已删除')
  await loadEvidences()
}

onMounted(loadEvidences)
</script>
