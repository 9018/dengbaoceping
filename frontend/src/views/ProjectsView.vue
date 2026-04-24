<template>
  <AppShell title="项目列表" subtitle="以项目为中心统一进入设备、证据、复核、记录与导出流程。">
    <div class="page-stack">
      <StatsCards :items="summaryCards" @select="handleStatSelect" />

      <el-card>
        <template #header>
          <div class="toolbar">
            <div>
              <div class="section-title">项目管理</div>
              <div class="section-subtitle">统一维护项目台账、状态和工作台入口。</div>
            </div>
            <el-space>
              <el-button @click="refresh">刷新</el-button>
              <el-button type="primary" @click="openCreate">新建项目</el-button>
            </el-space>
          </div>
        </template>

        <el-form inline class="filter-bar">
          <el-form-item label="状态">
            <el-select v-model="statusFilter" clearable placeholder="全部状态" style="width: 180px">
              <el-option v-for="status in projectStatusOptions" :key="status" :label="getStatusLabel('project', status)" :value="status" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input v-model="keyword" clearable placeholder="搜索项目名称、编码、说明" style="width: 280px" />
          </el-form-item>
        </el-form>

        <el-table :data="filteredProjects" border>
          <el-table-column prop="name" label="项目名称" min-width="200" />
          <el-table-column prop="code" label="项目编码" min-width="140" />
          <el-table-column prop="project_type" label="项目类型" min-width="160" />
          <el-table-column label="状态" width="120">
            <template #default="scope">
              <AppStatusTag kind="project" :status="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="description" label="项目说明" min-width="260" show-overflow-tooltip />
          <el-table-column prop="updated_at" label="更新时间" min-width="180" />
          <el-table-column label="操作" min-width="280" fixed="right">
            <template #default="scope">
              <el-space wrap>
                <el-button size="small" type="primary" @click="goDetail(scope.row.id)">进入工作台</el-button>
                <el-button size="small" @click="openEdit(scope.row)">编辑</el-button>
                <el-popconfirm title="确认删除该项目？" @confirm="removeProject(scope.row.id)">
                  <template #reference>
                    <el-button size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <ProjectFormDialog v-model="dialogVisible" :project="editingProject" :mode="dialogMode" @submit="submitProject" />
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import AppStatusTag from '@/components/AppStatusTag.vue'
import ProjectFormDialog from '@/components/ProjectFormDialog.vue'
import StatsCards, { type StatsCardItem } from '@/components/StatsCards.vue'
import { createProject, deleteProject, updateProject } from '@/api/projects'
import { useAppStore } from '@/stores/app'
import { useProjectsStore } from '@/stores/projects'
import { projectStatusOptions } from '@/utils/constants'
import { getStatusLabel } from '@/utils/status'
import type { Project } from '@/types/domain'

const router = useRouter()
const projectsStore = useProjectsStore()
const appStore = useAppStore()
const projects = ref<Project[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingProject = ref<Project | null>(null)
const statusFilter = ref('')
const keyword = ref('')

const summaryCards = computed<StatsCardItem[]>(() => [
  { label: '项目总数', value: projects.value.length, tip: '全部项目台账', to: '/projects', tone: 'primary' },
  { label: '进行中', value: projects.value.filter((item) => item.status === 'active').length, tip: '当前重点交付项目', to: '/projects', tone: 'success' },
  { label: '草稿', value: projects.value.filter((item) => item.status === 'draft').length, tip: '待继续推进', to: '/projects', tone: 'warning' },
  { label: '已归档', value: projects.value.filter((item) => item.status === 'archived').length, tip: '已完成闭环', to: '/projects', tone: 'default' },
])

const filteredProjects = computed(() => {
  const search = keyword.value.trim().toLowerCase()
  return projects.value.filter((item) => {
    const matchStatus = !statusFilter.value || item.status === statusFilter.value
    const matchKeyword =
      !search ||
      [item.name, item.code, item.description]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(search))
    return matchStatus && matchKeyword
  })
})

async function refresh() {
  appStore.setLoading(true)
  try {
    projects.value = await projectsStore.refreshProjects()
  } finally {
    appStore.setLoading(false)
  }
}

function openCreate() {
  dialogMode.value = 'create'
  editingProject.value = null
  dialogVisible.value = true
}

function openEdit(project: Project) {
  dialogMode.value = 'edit'
  editingProject.value = project
  dialogVisible.value = true
}

async function submitProject(payload: Record<string, unknown>) {
  if (!payload.name) {
    ElMessage.warning('项目名称不能为空')
    return
  }
  if (dialogMode.value === 'create') {
    await createProject(payload as never)
    ElMessage.success('项目创建成功')
  } else if (editingProject.value) {
    await updateProject(editingProject.value.id, payload)
    ElMessage.success('项目更新成功')
  }
  dialogVisible.value = false
  await refresh()
}

function goDetail(projectId: string) {
  router.push(`/projects/${projectId}`)
}

async function removeProject(projectId: string) {
  await deleteProject(projectId)
  ElMessage.success('项目已删除')
  await refresh()
}

function handleStatSelect(item: StatsCardItem) {
  if (!item.to) return
  router.push(item.to)
}

onMounted(refresh)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.filter-bar {
  margin-bottom: 16px;
}
</style>
