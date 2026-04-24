<template>
  <AppShell :project-id="projectId" title="记录中心" subtitle="查看 EvaluationRecord 列表、编辑 final_content、标记已复核、导出项目结果">
    <el-space direction="vertical" fill size="16">
      <el-card>
        <template #header>
          <div class="toolbar">
            <span>记录操作</span>
            <el-space>
              <el-button @click="loadData">刷新</el-button>
              <el-button type="primary" @click="generateDialogVisible = true">生成测评记录</el-button>
              <el-tooltip :disabled="canCreateExport" :content="getExportDisabledReason()" placement="top">
                <span class="action-wrapper">
                  <el-button type="success" :disabled="!canCreateExport" @click="createExportJob">导出项目结果</el-button>
                </span>
              </el-tooltip>
            </el-space>
          </div>
        </template>
        <el-form inline>
          <el-form-item label="选择证据">
            <el-select v-model="generateEvidenceId" placeholder="请选择证据" style="width: 280px">
              <el-option v-for="item in evidences" :key="item.id" :label="`${item.title} (${item.device || '未绑定设备'})`" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="设备类型覆盖">
            <el-input v-model="deviceTypeOverride" placeholder="可留空" style="width: 180px" />
          </el-form-item>
        </el-form>
      </el-card>

      <el-card>
        <template #header>
          <div class="toolbar">
            <span>记录列表</span>
            <span class="table-summary">共 {{ filteredRecords.length }} / {{ records.length }} 条</span>
          </div>
        </template>
        <el-form inline class="filter-form">
          <el-form-item label="状态筛选">
            <el-select v-model="statusFilter" clearable placeholder="全部状态" style="width: 180px">
              <el-option v-for="item in recordStatusOptions" :key="item" :label="getRecordStatusLabel(item)" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input v-model="keywordFilter" clearable placeholder="搜索标题/模板/测评项" style="width: 260px" />
          </el-form-item>
          <el-form-item>
            <el-button @click="resetFilters">重置筛选</el-button>
          </el-form-item>
        </el-form>
        <el-table :data="filteredRecords" border>
          <el-table-column prop="title" label="记录标题" min-width="200" />
          <el-table-column label="状态" width="120">
            <template #default="scope">
              <el-tag :type="getRecordStatusTagType(scope.row.status)" effect="light">{{ getRecordStatusLabel(scope.row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="match_score" label="匹配得分" width="120" />
          <el-table-column prop="template_code" label="模板编码" width="160" />
          <el-table-column prop="item_code" label="测评项编码" width="160" />
          <el-table-column prop="final_content" label="最终正文" min-width="260" show-overflow-tooltip />
          <el-table-column label="操作" min-width="460" fixed="right">
            <template #default="scope">
              <el-space wrap>
                <el-button size="small" @click="openEditor(scope.row)">编辑</el-button>
                <el-tooltip :disabled="canMarkReviewed(scope.row.status)" :content="getMarkReviewedDisabledReason(scope.row.status)" placement="top">
                  <span class="action-wrapper">
                    <el-button size="small" type="primary" :disabled="!canMarkReviewed(scope.row.status)" @click="quickReview(scope.row.id, 'reviewed')">标记已复核</el-button>
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

      <el-card v-if="exportJobs.length">
        <template #header>
          <span>导出任务</span>
        </template>
        <el-table :data="exportJobs" border>
          <el-table-column prop="file_name" label="文件名" min-width="240" />
          <el-table-column label="状态" width="120">
            <template #default="scope">
              <el-tag :type="getExportStatusTagType(scope.row.status)" effect="light">{{ getExportStatusLabel(scope.row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="record_count" label="记录数" width="120" />
          <el-table-column prop="file_size" label="文件大小" width="120" />
          <el-table-column label="下载" width="120">
            <template #default="scope">
              <el-link :href="getExportDownloadUrl(scope.row.id)" target="_blank" type="primary">下载</el-link>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card v-if="auditLogs.length">
        <template #header>
          <span>记录审计日志</span>
        </template>
        <el-timeline>
          <el-timeline-item v-for="log in auditLogs" :key="log.id" :timestamp="log.created_at">
            <div>{{ log.action }} / {{ log.reviewed_by || '未填写复核人' }}</div>
            <div class="timeline-comment">{{ log.review_comment || '无复核意见' }}</div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </el-space>

    <RecordEditDrawer v-model="drawerVisible" :record="editingRecord" @save="saveRecord" />

    <el-dialog v-model="generateDialogVisible" title="生成测评记录" width="520px">
      <el-form label-width="110px">
        <el-form-item label="证据">
          <el-select v-model="generateEvidenceId" placeholder="请选择证据" class="w-full">
            <el-option v-for="item in evidences" :key="item.id" :label="item.title" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="设备类型覆盖">
          <el-input v-model="deviceTypeOverride" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="generateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="generateNewRecord">生成</el-button>
      </template>
    </el-dialog>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import RecordEditDrawer from '@/components/RecordEditDrawer.vue'
import { listEvidences } from '@/api/evidences'
import { createProjectExport, getExportDownloadUrl, listProjectExports } from '@/api/exports'
import { generateRecord, listRecordAuditLogs, listRecords, reviewRecord, updateRecord } from '@/api/records'
import { recordStatusOptions } from '@/utils/constants'
import type { AuditLog, EvaluationRecord, Evidence, ExportJob } from '@/types/domain'

const props = defineProps<{ projectId: string }>()
const records = ref<EvaluationRecord[]>([])
const evidences = ref<Evidence[]>([])
const exportJobs = ref<ExportJob[]>([])
const auditLogs = ref<AuditLog[]>([])
const drawerVisible = ref(false)
const editingRecord = ref<EvaluationRecord | null>(null)
const generateDialogVisible = ref(false)
const generateEvidenceId = ref('')
const deviceTypeOverride = ref('')
const statusFilter = ref('')
const keywordFilter = ref('')

const recordStatusLabelMap: Record<string, string> = {
  generated: '待复核',
  reviewed: '已复核',
  approved: '已审批',
  exported: '已导出',
}

const exportStatusLabelMap: Record<string, string> = {
  completed: '已完成',
  pending: '处理中',
  failed: '失败',
}

const filteredRecords = computed(() => {
  const keyword = keywordFilter.value.trim().toLowerCase()
  return records.value.filter((item) => {
    const matchStatus = !statusFilter.value || item.status === statusFilter.value
    const matchKeyword =
      !keyword ||
      [item.title, item.template_code, item.item_code]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(keyword))
    return matchStatus && matchKeyword
  })
})

const canCreateExport = computed(() => records.value.length > 0 && records.value.every((item) => ['approved', 'exported'].includes(item.status)))

async function loadData() {
  const [recordsResult, evidencesResult, exportsResult] = await Promise.all([
    listRecords(props.projectId),
    listEvidences(props.projectId),
    listProjectExports(props.projectId).catch(() => ({ data: [] })),
  ])
  records.value = recordsResult.data
  evidences.value = evidencesResult.data
  exportJobs.value = exportsResult.data
  if (!generateEvidenceId.value) {
    generateEvidenceId.value = evidences.value[0]?.id || ''
  }
}

function openEditor(record: EvaluationRecord) {
  editingRecord.value = record
  drawerVisible.value = true
}

function resetFilters() {
  statusFilter.value = ''
  keywordFilter.value = ''
}

function getRecordStatusLabel(status: string) {
  return recordStatusLabelMap[status] || status
}

function getRecordStatusTagType(status: string) {
  if (status === 'generated') return 'warning'
  if (status === 'reviewed') return 'primary'
  if (status === 'approved') return 'success'
  return 'info'
}

function canMarkReviewed(status: string) {
  return status === 'generated'
}

function getMarkReviewedDisabledReason(status: string) {
  return canMarkReviewed(status) ? '' : '仅待复核记录可标记已复核'
}

function canApprove(status: string) {
  return status === 'reviewed'
}

function getApproveDisabledReason(status: string) {
  return canApprove(status) ? '' : '仅已复核记录可审批通过'
}

function getExportDisabledReason() {
  if (!records.value.length) return '暂无记录可导出'
  return '仅全部记录已审批后才可导出'
}

function getExportStatusLabel(status: string) {
  return exportStatusLabelMap[status] || status
}

function getExportStatusTagType(status: string) {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'danger'
  return 'warning'
}

async function saveRecord(payload: Record<string, unknown>) {
  if (!editingRecord.value) return
  await updateRecord(editingRecord.value.id, payload)
  ElMessage.success('记录更新成功')
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
    force_regenerate: false,
  })
  ElMessage.success('测评记录生成成功')
  generateDialogVisible.value = false
  await loadData()
}

async function createExportJob() {
  await createProjectExport(props.projectId, { format: 'txt' })
  ElMessage.success('项目导出成功')
  await loadData()
}

async function loadRecordAudit(recordId: string) {
  const { data } = await listRecordAuditLogs(recordId)
  auditLogs.value = data
}

onMounted(loadData)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.filter-form {
  margin-bottom: 16px;
}

.table-summary {
  color: #909399;
  font-size: 13px;
}

.timeline-comment {
  color: #909399;
  margin-top: 4px;
}

.w-full {
  width: 100%;
}

.action-wrapper {
  display: inline-flex;
}
</style>
