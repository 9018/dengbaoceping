<template>
  <AppShell :project-id="projectId" title="导出中心页" subtitle="聚焦导出门槛、导出任务历史和交付文件下载，形成最终交付闭环。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">Delivery Hub</div>
            <div class="section-title">交付出包控制台</div>
            <div class="section-subtitle">把导出门槛、阻塞项和导出历史收敛到同一页面，确保出包动作具备可审计性。</div>
          </div>
          <el-space wrap>
            <el-button @click="loadData">刷新</el-button>
            <el-tooltip :disabled="canCreateExport" :content="getExportDisabledReason()" placement="top">
              <span class="action-wrapper">
                <el-button type="success" :disabled="!canCreateExport" @click="createExportJob">导出项目结果</el-button>
              </span>
            </el-tooltip>
          </el-space>
        </div>
        <StatsCards :items="summaryCards" />
      </section>

      <el-card>
        <template #header>
          <div class="section-header">
            <div class="section-title">导出准备度</div>
            <div class="section-subtitle">只有全部记录已审批或已导出时，才能创建导出任务。</div>
          </div>
        </template>

        <div class="readiness-panel">
          <div class="readiness-panel__label">当前导出状态</div>
          <div class="readiness-panel__value">{{ canCreateExport ? '满足导出条件' : '仍有记录待处理' }}</div>
          <div class="readiness-panel__meta">
            <span>记录总数：{{ records.length }}</span>
            <span>已审批/导出：{{ readyRecordsCount }}</span>
            <span>待处理：{{ blockedRecords.length }}</span>
          </div>
        </div>

        <el-table v-if="blockedRecords.length" :data="blockedRecords" border>
          <el-table-column prop="title" label="记录标题" min-width="220" />
          <el-table-column label="当前状态" width="140">
            <template #default="scope">
              <AppStatusTag kind="record" :status="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" min-width="180" />
          <el-table-column label="阻塞说明" min-width="180">
            <template #default="scope">
              {{ getBlockedHint(scope.row.status) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default>
              <el-button size="small" type="primary" @click="go(`/projects/${projectId}/records`)">去处理</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card>
        <template #header>
          <div class="section-header">
            <div class="section-title">导出任务历史</div>
            <div class="section-subtitle">查看导出状态、文件信息和下载入口。</div>
          </div>
        </template>
        <el-table :data="exportJobs" border>
          <el-table-column prop="file_name" label="文件名" min-width="240" />
          <el-table-column label="状态" width="120">
            <template #default="scope">
              <AppStatusTag kind="export" :status="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="record_count" label="记录数" width="120" />
          <el-table-column prop="file_size" label="文件大小" width="120" />
          <el-table-column prop="updated_at" label="更新时间" min-width="180" />
          <el-table-column label="下载" width="120">
            <template #default="scope">
              <el-link :href="getExportDownloadUrl(scope.row.id)" target="_blank" type="primary">下载</el-link>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import AppStatusTag from '@/components/AppStatusTag.vue'
import StatsCards, { type StatsCardItem } from '@/components/StatsCards.vue'
import { createProjectExport, getExportDownloadUrl, listProjectExports } from '@/api/exports'
import { listRecords } from '@/api/records'
import type { EvaluationRecord, ExportJob } from '@/types/domain'

const props = defineProps<{ projectId: string }>()
const router = useRouter()
const records = ref<EvaluationRecord[]>([])
const exportJobs = ref<ExportJob[]>([])

const blockedRecords = computed(() => records.value.filter((item) => !['approved', 'exported'].includes(item.status)))
const readyRecordsCount = computed(() => records.value.length - blockedRecords.value.length)
const canCreateExport = computed(() => records.value.length > 0 && blockedRecords.value.length === 0)

const summaryCards = computed<StatsCardItem[]>(() => [
  { label: '导出任务', value: exportJobs.value.length, tip: '项目导出历史', tone: 'primary' },
  { label: '可导出记录', value: readyRecordsCount.value, tip: '已审批或已导出', tone: 'success' },
  { label: '待处理记录', value: blockedRecords.value.length, tip: '需要先完成记录闭环', tone: 'warning' },
  { label: '最新文件', value: exportJobs.value[0]?.file_name || '-', tip: '最近一次导出结果', tone: 'default' },
])

async function loadData() {
  const [recordsResult, exportsResult] = await Promise.all([
    listRecords(props.projectId),
    listProjectExports(props.projectId).catch(() => ({ data: [] })),
  ])
  records.value = recordsResult.data
  exportJobs.value = exportsResult.data
}

function getExportDisabledReason() {
  if (!records.value.length) return '暂无记录可导出'
  return '仍有记录未完成审批，无法导出'
}

function getBlockedHint(status: string) {
  if (status === 'generated') return '先进入记录页完成复核。'
  if (status === 'reviewed') return '还差审批通过，暂时不能导出。'
  return '当前记录状态尚未满足导出要求。'
}

async function createExportJob() {
  await createProjectExport(props.projectId, { format: 'txt' })
  ElMessage.success('项目导出成功')
  await loadData()
}

function go(path: string) {
  router.push(path)
}

onMounted(loadData)
</script>
