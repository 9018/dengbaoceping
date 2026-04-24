<template>
  <AppShell :project-id="projectId" title="证据管理" subtitle="上传证据、查看证据列表、触发 OCR 和字段抽取">
    <el-space direction="vertical" fill size="16">
      <el-card>
        <template #header>
          <div class="toolbar">
            <span>证据列表</span>
            <el-space>
              <el-button @click="loadEvidences">刷新</el-button>
              <el-button type="primary" @click="dialogVisible = true">上传证据</el-button>
            </el-space>
          </div>
        </template>

        <el-table :data="evidences" border>
          <el-table-column prop="title" label="证据标题" min-width="180" />
          <el-table-column prop="device" label="关联设备" min-width="140" />
          <el-table-column prop="evidence_type" label="类型" width="120" />
          <el-table-column label="OCR 状态" width="150">
            <template #default="scope">
              <el-tag :type="getOcrStatusTagType(scope.row.ocr_status)" effect="light">{{ getOcrStatusLabel(scope.row.ocr_status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="OCR Provider" width="140">
            <template #default="scope">
              {{ scope.row.ocr_provider || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="summary" label="摘要" min-width="220" show-overflow-tooltip />
          <el-table-column label="操作" min-width="500" fixed="right">
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

      <el-card>
        <template #header>
          <span>操作参数</span>
        </template>
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
        </el-form>
      </el-card>
    </el-space>

    <EvidenceUploadDialog v-model="dialogVisible" @submit="submitUpload" />
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import EvidenceUploadDialog from '@/components/EvidenceUploadDialog.vue'
import { deleteEvidence, extractFields, listEvidences, runOcr, uploadEvidence } from '@/api/evidences'
import { ocrSampleOptions, templateCodeOptions } from '@/utils/constants'
import type { Evidence } from '@/types/domain'

const props = defineProps<{ projectId: string }>()
const router = useRouter()
const evidences = ref<Evidence[]>([])
const dialogVisible = ref(false)
const selectedSampleId = ref('firewall_basic')
const selectedTemplateCode = ref('security_device_basic')

const ocrStatusLabelMap: Record<string, string> = {
  completed: '已完成',
  pending: '处理中',
  failed: '失败',
}

async function loadEvidences() {
  const { data } = await listEvidences(props.projectId)
  evidences.value = data
}

function getOcrStatusLabel(status: string | null) {
  if (!status) return '未执行'
  return ocrStatusLabelMap[status] || status
}

function getOcrStatusTagType(status: string | null) {
  if (!status) return 'info'
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'danger'
  return 'warning'
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

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.action-wrapper {
  display: inline-flex;
}
</style>
