<template>
  <AppShell :project-id="projectId" title="测评记录页" subtitle="按设备和状态聚焦记录复核，编辑 final_content 并推进审批闭环。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">Record Review</div>
            <div class="section-title">测评记录审批工作区</div>
            <div class="section-subtitle">以项目范围为基础，叠加设备与状态筛选，聚焦 final_content 修订与状态流转。</div>
          </div>
          <el-space wrap>
            <el-button @click="loadData">刷新</el-button>
            <el-button type="primary" @click="generateDialogVisible = true">生成测评记录</el-button>
            <el-button type="success" @click="go(`/projects/${projectId}/exports`)">进入导出中心</el-button>
          </el-space>
        </div>
        <StatsCards :items="summaryCards" />
      </section>

      <el-card>
        <template #header>
          <div class="section-header">
            <div class="section-title">记录生成与筛选</div>
            <div class="section-subtitle">把设备筛选、状态筛选、快速复核和审批动作收敛到同一主表格。</div>
          </div>
        </template>

        <div class="page-filter-bar">
          <el-form inline>
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
              <el-input v-model="keywordFilter" clearable placeholder="搜索标题/模板/测评项" style="width: 260px" />
            </el-form-item>
          </el-form>
        </div>

        <el-table :data="filteredRecords" border>
          <el-table-column prop="title" label="记录标题" min-width="200" />
          <el-table-column prop="device_name" label="设备" min-width="160" />
          <el-table-column label="状态" width="130">
            <template #default="scope">
              <AppStatusTag kind="record" :status="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="match_score" label="匹配得分" width="120" />
          <el-table-column prop="template_code" label="模板编码" width="170" />
          <el-table-column prop="item_code" label="测评项编码" width="170" />
          <el-table-column label="审批建议" min-width="180">
            <template #default="scope">
              {{ getRecordHint(scope.row.status) }}
            </template>
          </el-table-column>
          <el-table-column prop="final_content" label="最终正文" min-width="280" show-overflow-tooltip />
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
import { generateRecord, listRecordAuditLogs, listRecords, reviewRecord, updateRecord } from '@/api/records'
import { recordStatusOptions } from '@/utils/constants'
import { getStatusLabel } from '@/utils/status'
import type { Asset, AuditLog, EvaluationRecord, Evidence } from '@/types/domain'

interface RecordViewItem extends EvaluationRecord {
  device_name: string
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
const statusFilter = ref('')
const deviceFilter = ref('')
const keywordFilter = ref('')

const recordRows = computed<RecordViewItem[]>(() => {
  const evidenceMap = new Map(evidences.value.map((item) => [item.id, item]))
  const assetMap = new Map(assets.value.map((item) => [item.id, item]))
  return records.value.map((record) => {
    const firstEvidence = record.evidence_ids.map((id) => evidenceMap.get(id)).find(Boolean)
    const asset = record.asset_id ? assetMap.get(record.asset_id) : undefined
    return {
      ...record,
      device_name: firstEvidence?.device || asset?.filename || '未绑定设备',
    }
  })
})

const deviceOptions = computed(() => Array.from(new Set(recordRows.value.map((item) => item.device_name).filter(Boolean))))

const summaryCards = computed<StatsCardItem[]>(() => [
  { label: '记录总数', value: records.value.length, tip: '当前项目全部测评记录', tone: 'primary' },
  { label: '待复核', value: records.value.filter((item) => item.status === 'generated').length, tip: '需要先标记复核', tone: 'warning' },
  { label: '已复核', value: records.value.filter((item) => item.status === 'reviewed').length, tip: '可继续审批', tone: 'success' },
  { label: '已审批/导出', value: records.value.filter((item) => ['approved', 'exported'].includes(item.status)).length, tip: '进入导出闭环', tone: 'default' },
])

const filteredRecords = computed(() => {
  const keyword = keywordFilter.value.trim().toLowerCase()
  return recordRows.value.filter((item) => {
    const matchStatus = !statusFilter.value || item.status === statusFilter.value
    const matchDevice = !deviceFilter.value || item.device_name === deviceFilter.value
    const matchKeyword =
      !keyword ||
      [item.title, item.template_code, item.item_code]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(keyword))
    return matchStatus && matchDevice && matchKeyword
  })
})

async function loadData() {
  const [recordsResult, evidencesResult, assetsResult] = await Promise.all([
    listRecords(props.projectId),
    listEvidences(props.projectId),
    listAssets(props.projectId),
  ])
  records.value = recordsResult.data
  evidences.value = evidencesResult.data
  assets.value = assetsResult.data
  if (!generateEvidenceId.value) {
    generateEvidenceId.value = evidences.value[0]?.id || ''
  }
}

function openEditor(record: EvaluationRecord) {
  editingRecord.value = record
  drawerVisible.value = true
}

function getRecordHint(status: string) {
  if (status === 'generated') return '先检查 final_content，再标记复核。'
  if (status === 'reviewed') return '复核完成后可继续审批通过。'
  if (status === 'approved') return '已满足导出门槛，等待出包。'
  return '记录已进入导出闭环。'
}

function canMarkReviewed(status: string) {
  return status === 'generated'
}

function getMarkReviewedDisabledReason(status: string) {
  return canMarkReviewed(status) ? '' : '仅待复核记录可标记复核'
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

async function loadRecordAudit(recordId: string) {
  const { data } = await listRecordAuditLogs(recordId)
  auditLogs.value = data
}

function go(path: string) {
  router.push(path)
}

onMounted(loadData)
</script>
