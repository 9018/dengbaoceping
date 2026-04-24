<template>
  <AppShell title="项目列表" subtitle="查看项目列表、新建项目、进入项目详情">
    <el-card>
      <template #header>
        <div class="toolbar">
          <span>项目管理</span>
          <el-space>
            <el-button @click="refresh">刷新</el-button>
            <el-button type="primary" @click="openCreate">新建项目</el-button>
          </el-space>
        </div>
      </template>

      <el-table :data="projects" border>
        <el-table-column prop="code" label="项目编码" min-width="140" />
        <el-table-column prop="name" label="项目名称" min-width="200" />
        <el-table-column prop="project_type" label="项目类型" min-width="160" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="description" label="项目说明" min-width="220" show-overflow-tooltip />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="scope">
            <el-space>
              <el-button size="small" type="primary" @click="goDetail(scope.row.id)">详情</el-button>
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
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import ProjectFormDialog from '@/components/ProjectFormDialog.vue'
import { createProject, deleteProject, updateProject } from '@/api/projects'
import { useProjectsStore } from '@/stores/projects'
import { useAppStore } from '@/stores/app'
import type { Project } from '@/types/domain'

const router = useRouter()
const projectsStore = useProjectsStore()
const appStore = useAppStore()
const projects = ref<Project[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingProject = ref<Project | null>(null)

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

onMounted(refresh)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
