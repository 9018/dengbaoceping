<template>
  <AppShell title="工作台 Dashboard" subtitle="以项目、证据、OCR、复核和导出为主线，建立等级保护测评交付闭环。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">Command Center</div>
            <div class="section-title">全局交付驾驶舱</div>
            <div class="section-subtitle">围绕项目闭环、待办压力与关键入口做统一调度，优先聚焦待 OCR、待字段复核、待记录审批三类任务。</div>
          </div>
          <el-space wrap>
            <el-button type="primary" @click="go('/projects')">进入项目列表</el-button>
            <el-button @click="go('/template-rules')">查看模板规则</el-button>
          </el-space>
        </div>
        <StatsCards :items="summaryCards" @select="handleStatSelect" />
      </section>

      <section class="page-grid-2">
        <el-card>
          <template #header>
            <div class="card-toolbar">
              <div class="section-header">
                <div class="section-title">测评流程进度</div>
                <div class="section-subtitle">按项目建档、证据采集、OCR、字段复核、记录复核、项目导出六步拉通过程追踪。</div>
              </div>
            </div>
          </template>

          <div class="highlight-panel">
            <div class="panel-label">当前闭环阶段</div>
            <div class="panel-value">{{ workflowStepLabel }}</div>
            <div class="panel-meta">只要仍有待处理记录或识别任务，Dashboard 就持续把注意力拉回关键阻塞点。</div>
          </div>

          <div class="flow-grid workflow-panel">
            <div v-for="(step, index) in workflowSteps" :key="step" class="flow-step">
              <div class="flow-step__index">{{ index + 1 }}</div>
              <div class="flow-step__title">{{ step }}</div>
              <div class="flow-step__meta">{{ getWorkflowMeta(index) }}</div>
            </div>
          </div>
        </el-card>

        <el-card>
          <template #header>
            <div class="section-header">
              <div class="section-title">当前重点</div>
              <div class="section-subtitle">把最影响交付闭环的工作项放到同一视野内。</div>
            </div>
          </template>
          <div class="focus-grid">
            <div class="metric-panel metric-panel--warning">
              <div class="panel-label">待 OCR</div>
              <div class="panel-value">{{ pendingOcrCount }}</div>
              <div class="panel-meta">仍需先完成识别的证据数量。</div>
            </div>
            <div class="metric-panel">
              <div class="panel-label">待字段复核</div>
              <div class="panel-value">{{ pendingFieldReviewCount }}</div>
              <div class="panel-meta">已完成 OCR 但仍待进入字段确认的证据。</div>
            </div>
            <div class="metric-panel metric-panel--success">
              <div class="panel-label">待记录审批</div>
              <div class="panel-value">{{ pendingRecordReviewCount }}</div>
              <div class="panel-meta">进入记录审校后，距离交付还差最后一跳。</div>
            </div>
          </div>
          <div class="notice-panel dashboard-note">
            <div class="notice-panel__label">工作建议</div>
            <div class="notice-panel__value">{{ nextActionSummary }}</div>
            <div class="notice-panel__meta">
              <span>项目总数：{{ totalProjects }}</span>
              <span>活跃项目：{{ activeProjects }}</span>
            </div>
          </div>
        </el-card>
      </section>

      <el-card>
        <template #header>
          <div class="card-toolbar">
            <div class="section-header">
              <div class="section-title">项目总览</div>
              <div class="section-subtitle">聚焦项目状态、待复核压力和直达工作台入口。</div>
            </div>
            <el-button @click="loadDashboard">刷新数据</el-button>
          </div>
        </template>
        <el-table :data="projectRows" border>
          <el-table-column prop="name" label="项目名称" min-width="180" />
          <el-table-column prop="code" label="项目编码" min-width="140" />
          <el-table-column label="项目状态" width="130">
            <template #default="scope">
              <AppStatusTag kind="project" :status="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="evidenceCount" label="证据数" width="100" />
          <el-table-column prop="ocrDoneCount" label="OCR完成" width="110" />
          <el-table-column prop="recordCount" label="记录数" width="100" />
          <el-table-column prop="pendingReviewCount" label="待复核" width="100" />
          <el-table-column label="行动建议" min-width="180">
            <template #default="scope">
              {{ getProjectAction(scope.row) }}
            </template>
          </el-table-column>
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

const workflowStepLabel = computed(() => workflowSteps[Math.min(workflowActive.value, workflowSteps.length - 1)] || '等待项目启动')

const nextActionSummary = computed(() => {
  if (pendingRecordReviewCount.value > 0) return '优先处理测评记录审批，把导出阻塞项清零。'
  if (pendingFieldReviewCount.value > 0) return '优先进入识别复核页，补齐字段确认与修正。'
  if (pendingOcrCount.value > 0) return '优先推进证据 OCR，把识别阶段快速拉通。'
  if (totalProjects.value > 0) return '当前项目已基本跑通，可以抽查规则与导出质量。'
  return '先创建项目，启动等级保护测评工作台。'
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

function getWorkflowMeta(index: number) {
  if (index === 0) return `${totalProjects.value} 个项目已纳入工作台`
  if (index === 1) return `${Object.values(evidencesByProject.value).flat().length} 份证据进入流程`
  if (index === 2) return `${pendingOcrCount.value} 份证据仍待识别`
  if (index === 3) return `${pendingFieldReviewCount.value} 份证据待字段确认`
  if (index === 4) return `${pendingRecordReviewCount.value} 条记录待审批`
  return '全部记录审批通过后进入交付导出'
}

function getProjectAction(project: DashboardProjectRow) {
  if (project.pendingReviewCount > 0) return '优先进入测评记录页处理审批阻塞。'
  if (project.evidenceCount > project.ocrDoneCount) return '优先推进证据 OCR 识别。'
  if (project.evidenceCount === 0) return '先补充证据，启动识别链路。'
  return '可抽查规则或准备导出。'
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
.workflow-panel {
  margin-top: 18px;
}

.dashboard-note {
  margin-top: 18px;
}
</style>
