<template>
  <AppShell :project-id="projectId" title="项目详情" subtitle="以项目为中心查看范围、状态、阶段进度和关键工作入口。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">Project Workbench</div>
            <div class="section-title">单项目总控台</div>
            <div class="section-subtitle">把项目概览、阶段推进、关键入口和交付抓手汇聚到同一页面，减少来回跳转成本。</div>
          </div>
          <el-space wrap>
            <el-button @click="loadData">刷新</el-button>
            <el-button type="primary" @click="go(`/projects/${projectId}/evidences`)">进入证据中心</el-button>
          </el-space>
        </div>
        <StatsCards :items="statsItems" @select="handleStatsSelect" />
      </section>

      <section class="page-grid-2">
        <el-card>
          <template #header>
            <div class="section-header">
              <div class="section-title">项目概览</div>
              <div class="section-subtitle">查看基础信息、项目状态和当前交付上下文。</div>
            </div>
          </template>

          <div class="workspace-summary">
            <div class="summary-item">
              <div class="summary-item__label">项目名称</div>
              <div class="summary-item__value summary-item__value--text">{{ project?.name || '-' }}</div>
              <div class="summary-item__meta">编码：{{ project?.code || '未设置' }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-item__label">项目状态</div>
              <div class="summary-item__value summary-item__value--tag">
                <AppStatusTag v-if="project" kind="project" :status="project.status" />
                <span v-else>-</span>
              </div>
              <div class="summary-item__meta">项目类型：{{ project?.project_type || '-' }}</div>
            </div>
          </div>

          <el-descriptions :column="2" border class="detail-descriptions">
            <el-descriptions-item label="项目名称">{{ project?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="项目编码">{{ project?.code || '-' }}</el-descriptions-item>
            <el-descriptions-item label="项目类型">{{ project?.project_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="当前阶段">{{ workflowStepLabel }}</el-descriptions-item>
            <el-descriptions-item label="项目说明" :span="2">{{ project?.description || '暂无说明' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card>
          <template #header>
            <div class="section-header">
              <div class="section-title">流程推进</div>
              <div class="section-subtitle">按当前数据状态识别项目所处阶段和下一步动作。</div>
            </div>
          </template>

          <div class="flow-grid">
            <div v-for="(step, index) in workflowSteps" :key="step" class="flow-step" :class="{ 'flow-step--active': workflowActive >= index }">
              <div class="flow-step__index">{{ index + 1 }}</div>
              <div class="flow-step__title">{{ step }}</div>
              <div class="flow-step__meta">{{ getStepHint(index) }}</div>
            </div>
          </div>
        </el-card>
      </section>

      <el-card>
        <template #header>
          <div class="section-header">
            <div class="section-title">工作台入口</div>
            <div class="section-subtitle">按角色和阶段进入对应工作区，确保每一步都有明确抓手。</div>
          </div>
        </template>
        <div class="entry-grid">
          <button v-for="entry in quickEntries" :key="entry.title" class="entry-card" type="button" @click="go(entry.to)">
            <div class="entry-card__title">{{ entry.title }}</div>
            <div class="entry-card__desc">{{ entry.description }}</div>
          </button>
        </div>
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
import { listAssets } from '@/api/assets'
import { listEvidences } from '@/api/evidences'
import { getProject } from '@/api/projects'
import { listRecords } from '@/api/records'
import { useAppStore } from '@/stores/app'
import { workflowSteps } from '@/utils/constants'
import type { Asset, Evidence, EvaluationRecord, Project } from '@/types/domain'

const props = defineProps<{ projectId: string }>()
const router = useRouter()
const appStore = useAppStore()
const project = ref<Project | null>(null)
const assets = ref<Asset[]>([])
const evidences = ref<Evidence[]>([])
const records = ref<EvaluationRecord[]>([])

const statsItems = computed<StatsCardItem[]>(() => [
  { label: '设备资产', value: assets.value.length, tip: '进入设备资产页', to: `/projects/${props.projectId}/assets`, tone: 'primary' },
  { label: '证据中心', value: evidences.value.length, tip: '进入证据中心页', to: `/projects/${props.projectId}/evidences`, tone: 'success' },
  { label: '测评记录', value: records.value.length, tip: '进入测评记录页', to: `/projects/${props.projectId}/records`, tone: 'default' },
  {
    label: '待闭环记录',
    value: records.value.filter((item) => !['approved', 'exported'].includes(item.status)).length,
    tip: '优先推进记录复核与导出',
    to: `/projects/${props.projectId}/records`,
    tone: 'warning',
  },
])

const workflowActive = computed(() => {
  if (records.value.some((item) => !['approved', 'exported'].includes(item.status))) return 4
  if (evidences.value.some((item) => item.ocr_status !== 'completed')) return 2
  if (evidences.value.length > 0) return 3
  if (assets.value.length > 0) return 1
  return 0
})

const workflowStepLabel = computed(() => workflowSteps[Math.min(workflowActive.value, workflowSteps.length - 1)] || '项目建档')

const quickEntries = computed(() => [
  { title: '设备资产页', description: '维护项目内设备资产、来源和入库状态。', to: `/projects/${props.projectId}/assets` },
  { title: '证据中心页', description: '上传证据并执行 OCR、字段抽取。', to: `/projects/${props.projectId}/evidences` },
  { title: '识别复核页', description: '三栏联动复核 OCR 文本和字段修正结果。', to: `/projects/${props.projectId}/review` },
  { title: '测评记录页', description: '编辑 final_content，完成复核审批。', to: `/projects/${props.projectId}/records` },
  { title: '导出中心页', description: '查看导出门槛、创建导出任务并下载结果。', to: `/projects/${props.projectId}/exports` },
  { title: '模板规则页', description: '查阅字段规则、测评项和模板内容。', to: '/template-rules' },
])

async function loadData() {
  appStore.setLoading(true)
  try {
    const [projectResult, assetsResult, evidencesResult, recordsResult] = await Promise.all([
      getProject(props.projectId),
      listAssets(props.projectId),
      listEvidences(props.projectId),
      listRecords(props.projectId),
    ])
    project.value = projectResult.data
    assets.value = assetsResult.data
    evidences.value = evidencesResult.data
    records.value = recordsResult.data
    appStore.setCurrentProject(projectResult.data)
  } finally {
    appStore.setLoading(false)
  }
}

function getStepHint(index: number) {
  if (index === 0) return project.value ? '项目已完成建档，可继续推进资产与证据。' : '先完成项目建档。'
  if (index === 1) return `${assets.value.length} 项资产已进入台账。`
  if (index === 2) return `${evidences.value.filter((item) => item.ocr_status !== 'completed').length} 份证据仍待 OCR。`
  if (index === 3) return `${evidences.value.length} 份证据可进入字段复核。`
  if (index === 4) return `${records.value.filter((item) => !['approved', 'exported'].includes(item.status)).length} 条记录待处理。`
  return '全部记录审批通过后即可进入项目导出。'
}

function go(path: string) {
  router.push(path)
}

function handleStatsSelect(item: StatsCardItem) {
  if (!item.to) return
  go(item.to)
}

onMounted(loadData)
</script>

<style scoped>
.detail-descriptions {
  margin-top: 18px;
}

.summary-item__value--text {
  font-size: 20px;
  line-height: 1.3;
}

.summary-item__value--tag {
  font-size: 16px;
}

.flow-step--active {
  border-color: rgba(37, 99, 235, 0.22);
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.98), rgba(247, 250, 252, 0.98));
}
</style>
