<template>
  <AppShell :project-id="projectId" title="项目详情" subtitle="显示项目基础信息、统计卡和业务入口">
    <el-space direction="vertical" fill size="16">
      <el-card>
        <template #header>
          <div class="toolbar">
            <span>项目基础信息</span>
            <el-space>
              <el-button @click="loadData">刷新</el-button>
              <el-button type="primary" @click="go(`/projects/${projectId}/evidences`)">上传/管理证据</el-button>
              <el-button type="success" @click="go(`/projects/${projectId}/records`)">进入记录中心</el-button>
            </el-space>
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="项目名称">{{ project?.name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="项目编码">{{ project?.code || '-' }}</el-descriptions-item>
          <el-descriptions-item label="项目类型">{{ project?.project_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="项目状态">
            <el-tag v-if="project?.status" :type="getProjectStatusTagType(project.status)" effect="light">{{ getProjectStatusLabel(project.status) }}</el-tag>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="项目说明" :span="2">{{ project?.description || '暂无说明' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <StatsCards :items="statsItems" @select="handleStatsSelect" />

      <el-card>
        <template #header>
          <span>快捷入口</span>
        </template>
        <el-space wrap>
          <el-button type="primary" @click="go(`/projects/${projectId}/assets`)">进入设备管理</el-button>
          <el-button type="primary" @click="go(`/projects/${projectId}/evidences`)">进入证据管理</el-button>
          <el-button type="primary" @click="go(`/projects/${projectId}/review`)">进入识别复核</el-button>
          <el-button type="primary" @click="go(`/projects/${projectId}/records`)">进入记录中心</el-button>
        </el-space>
      </el-card>
    </el-space>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import StatsCards from '@/components/StatsCards.vue'
import { getProject } from '@/api/projects'
import { listAssets } from '@/api/assets'
import { listEvidences } from '@/api/evidences'
import { listRecords } from '@/api/records'
import { useAppStore } from '@/stores/app'
import type { Asset, Evidence, EvaluationRecord, Project } from '@/types/domain'

const props = defineProps<{ projectId: string }>()
const router = useRouter()
const appStore = useAppStore()
const project = ref<Project | null>(null)
const assets = ref<Asset[]>([])
const evidences = ref<Evidence[]>([])
const records = ref<EvaluationRecord[]>([])

const projectStatusLabelMap: Record<string, string> = {
  draft: '草稿',
  active: '进行中',
  archived: '已归档',
}

const statsItems = computed(() => [
  { label: '设备数量', value: assets.value.length, tip: '点击进入资产列表', to: `/projects/${props.projectId}/assets` },
  { label: '证据数量', value: evidences.value.length, tip: '点击进入证据管理', to: `/projects/${props.projectId}/evidences` },
  { label: '记录数量', value: records.value.length, tip: '点击进入记录中心', to: `/projects/${props.projectId}/records` },
  {
    label: '未复核数量',
    value: records.value.filter((item) => !['approved', 'exported'].includes(item.status)).length,
    tip: '点击进入记录中心处理',
    to: `/projects/${props.projectId}/records`,
  },
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

function getProjectStatusLabel(status: string) {
  return projectStatusLabelMap[status] || status
}

function getProjectStatusTagType(status: string) {
  if (status === 'active') return 'success'
  if (status === 'archived') return 'info'
  return 'warning'
}

function go(path: string) {
  router.push(path)
}

function handleStatsSelect(item: { to?: string }) {
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
</style>
