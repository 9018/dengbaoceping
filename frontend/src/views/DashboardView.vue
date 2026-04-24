<template>
  <AppShell title="工作台 Dashboard" subtitle="以项目、证据、OCR、复核和导出为主线，建立等级保护测评交付闭环。">
    <div class="page-stack">
      <StatsCards :items="summaryCards" @select="handleStatSelect" />

      <el-row :gutter="16">
        <el-col :xs="24" :lg="15">
          <el-card>
            <template #header>
              <div class="card-header">
                <div>
                  <div class="section-title">测评流程进度</div>
                  <div class="section-subtitle">围绕关键节点进行过程追踪和结果闭环。</div>
                </div>
              </div>
            </template>
            <el-steps :active="workflowActive" finish-status="success" align-center>
              <el-step v-for="step in workflowSteps" :key="step" :title="step" />
            </el-steps>

            <div class="dashboard-actions">
              <el-button type="primary" @click="go('/projects')">进入项目列表</el-button>
              <el-button @click="go('/template-rules')">查看模板规则</el-button>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="9">
          <el-card>
            <template #header>
              <div>
                <div class="section-title">当前重点</div>
                <div class="section-subtitle">识别需要推进的项目状态，优先处理待复核任务。</div>
              </div>
            </template>
            <div class="focus-metrics">
              <div class="focus-metric">
                <span>待 OCR</span>
                <strong>{{ pendingOcrCount }}</strong>
              </div>
              <div class="focus-metric">
                <span>待字段复核</span>
                <strong>{{ pendingFieldReviewCount }}</strong>
              </div>
              <div class="focus-metric">
                <span>待记录审批</span>
                <strong>{{ pendingRecordReviewCount }}</strong>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card>
        <template #header>
          <div class="card-header">
            <div>
              <div class="section-title">项目总览</div>
              <div class="section-subtitle">聚焦项目状态、待复核压力和工作台入口。</div>
            </div>
            <el-button @click="loadDashboard">刷新数据</el-button>
          </div>
        </template>
        <el-table :data="projectRows" border>
          <el-table-column prop="name" label="项目名称" min-width="180" />
          <el-table-column prop="code" label="项目编码" min-width="140" />
          <el-table-column label="项目状态" width="120">
            <template #default="scope">
              <AppStatusTag kind="project" :status="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="evidenceCount" label="证据数" width="100" />
          <el-table-column prop="ocrDoneCount" label="OCR完成" width="110" />
          <el-table-column prop="recordCount" label="记录数" width="100" />
          <el-table-column prop="pendingReviewCount" label="待复核" width="100" />
          <el-table-column label="操作" min-width="260" fixed="right">
            <template #default="scope">
              <el-space wrap>
                <el-button size="small" type="primary" @click="go(`/projects/${scope.row.id}`)">项目详情</el-button>
                <el-button size="small" @click="go(`/projects/${scope.row.id}/review`)">识别复核</el-button>
                <el-button size="small" @click="go(`/projects/${scope.row.id}/records`)">测评记录</el-button>
              </el-space>
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
import AppShell from '@/components/AppShell.vue'
import AppStatusTag from '@/components/AppStatusTag.vue'
import StatsCards, { type StatsCardItem } from '@/components/StatsCards.vue'
import { listEvidences } from '@/api/evidences'
import { listProjects } from '@/api/projects'
import { listRecords } from '@/api/records'
import { workflowSteps } from '@/utils/constants'
import type { Evidence, EvaluationRecord, Project } from '@/types/domain'

interface DashboardProjectRow extends Project {
  evidenceCount: number
  ocrDoneCount: number
  recordCount: number
  pendingReviewCount: number
}

const router = useRouter()
const projectRows = ref<DashboardProjectRow[]>([])
const evidencesByProject = ref<Record<string, Evidence[]>>({})
const recordsByProject = ref<Record<string, EvaluationRecord[]>>({})

const totalProjects = computed(() => projectRows.value.length)
const activeProjects = computed(() => projectRows.value.filter((item) => item.status === 'active').length)
const pendingOcrCount = computed(() => Object.values(evidencesByProject.value).flat().filter((item) => item.ocr_status !== 'completed').length)
const pendingFieldReviewCount = computed(() => Object.values(evidencesByProject.value).flat().filter((item) => item.ocr_status === 'completed' && !item.text_content).length)
const pendingRecordReviewCount = computed(() => Object.values(recordsByProject.value).flat().filter((item) => !['approved', 'exported'].includes(item.status)).length)

const workflowActive = computed(() => {
  if (pendingRecordReviewCount.value > 0) return 4
  if (pendingFieldReviewCount.value > 0) return 3
  if (pendingOcrCount.value > 0) return 2
  if (totalProjects.value > 0) return 1
  return 0
})

const summaryCards = computed<StatsCardItem[]>(() => [
  { label: '项目总数', value: totalProjects.value, tip: '查看项目台账', to: '/projects', tone: 'primary' },
  { label: '活跃项目', value: activeProjects.value, tip: '聚焦进行中项目', to: '/projects', tone: 'success' },
  { label: '待 OCR', value: pendingOcrCount.value, tip: '优先推进证据识别', to: '/projects', tone: 'warning' },
  { label: '待记录复核', value: pendingRecordReviewCount.value, tip: '闭环前的最后抓手', to: '/projects', tone: 'default' },
])

async function loadDashboard() {
  const { data: projects } = await listProjects()
  const evidenceResults = await Promise.all(projects.map(async (project) => ({ projectId: project.id, response: await listEvidences(project.id).catch(() => ({ data: [] })) })))
  const recordResults = await Promise.all(projects.map(async (project) => ({ projectId: project.id, response: await listRecords(project.id).catch(() => ({ data: [] })) })))

  evidencesByProject.value = Object.fromEntries(evidenceResults.map((item) => [item.projectId, item.response.data]))
  recordsByProject.value = Object.fromEntries(recordResults.map((item) => [item.projectId, item.response.data]))

  projectRows.value = projects.map((project) => {
    const evidences = evidencesByProject.value[project.id] || []
    const records = recordsByProject.value[project.id] || []
    return {
      ...project,
      evidenceCount: evidences.length,
      ocrDoneCount: evidences.filter((item) => item.ocr_status === 'completed').length,
      recordCount: records.length,
      pendingReviewCount: records.filter((item) => !['approved', 'exported'].includes(item.status)).length,
    }
  })
}

function go(path: string) {
  router.push(path)
}

function handleStatSelect(item: StatsCardItem) {
  if (!item.to) return
  go(item.to)
}

onMounted(loadDashboard)
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.dashboard-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.focus-metrics {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.focus-metric {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-radius: 14px;
  background: #f8fbff;
  border: 1px solid #e5eef8;
}

.focus-metric span {
  color: #64748b;
}

.focus-metric strong {
  font-size: 22px;
  color: #0f172a;
}
</style>
