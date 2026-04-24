<template>
  <AppShell :project-id="projectId" title="项目详情" subtitle="以项目为中心查看范围、状态、阶段进度和关键工作入口。">
    <div class="page-stack">
      <StatsCards :items="statsItems" @select="handleStatsSelect" />

      <el-row :gutter="16">
        <el-col :xs="24" :xl="15">
          <el-card>
            <template #header>
              <div class="toolbar">
                <div>
                  <div class="section-title">项目概览</div>
                  <div class="section-subtitle">查看基础信息和当前阶段，拉通项目维度的交付抓手。</div>
                </div>
                <el-space>
                  <el-button @click="loadData">刷新</el-button>
                  <el-button type="primary" @click="go(`/projects/${projectId}/evidences`)">进入证据中心</el-button>
                </el-space>
              </div>
            </template>

            <el-descriptions :column="2" border>
              <el-descriptions-item label="项目名称">{{ project?.name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="项目编码">{{ project?.code || '-' }}</el-descriptions-item>
              <el-descriptions-item label="项目类型">{{ project?.project_type || '-' }}</el-descriptions-item>
              <el-descriptions-item label="项目状态">
                <AppStatusTag v-if="project" kind="project" :status="project.status" />
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item label="项目说明" :span="2">{{ project?.description || '暂无说明' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="9">
          <el-card>
            <template #header>
              <div>
                <div class="section-title">流程推进</div>
                <div class="section-subtitle">按当前数据状态识别项目所在阶段。</div>
              </div>
            </template>
            <el-steps direction="vertical" :active="workflowActive" finish-status="success">
              <el-step v-for="step in workflowSteps" :key="step" :title="step" />
            </el-steps>
          </el-card>
        </el-col>
      </el-row>

      <el-card>
        <template #header>
          <div>
            <div class="section-title">工作台入口</div>
            <div class="section-subtitle">按角色和阶段进入对应工作区。</div>
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
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.entry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.entry-card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid #dbe5f1;
  background: linear-gradient(180deg, #ffffff, #f8fbff);
  text-align: left;
  cursor: pointer;
}

.entry-card__title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.entry-card__desc {
  margin-top: 8px;
  color: #64748b;
  line-height: 1.6;
}
</style>
