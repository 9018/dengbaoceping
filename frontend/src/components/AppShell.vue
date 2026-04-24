<template>
  <el-container class="workspace-shell">
    <el-aside width="264px" class="workspace-shell__aside">
      <div class="workspace-shell__brand">
        <div class="workspace-shell__brand-mark">DP</div>
        <div>
          <div class="workspace-shell__brand-title">等级保护测评工作台</div>
          <div class="workspace-shell__brand-subtitle">Security Assessment Workspace</div>
        </div>
      </div>

      <div class="workspace-shell__menu-title">全局导航</div>
      <el-menu :default-active="activeMenu" router class="workspace-shell__menu">
        <el-menu-item index="/dashboard">工作台 Dashboard</el-menu-item>
        <el-menu-item index="/projects">项目列表</el-menu-item>
        <el-menu-item index="/template-rules">模板规则</el-menu-item>
      </el-menu>

      <template v-if="projectId">
        <div class="workspace-shell__menu-title">项目操作</div>
        <el-menu :default-active="activeMenu" router class="workspace-shell__menu workspace-shell__menu--project">
          <el-menu-item :index="`/projects/${projectId}`">项目详情</el-menu-item>
          <el-menu-item :index="`/projects/${projectId}/assets`">设备资产</el-menu-item>
          <el-menu-item :index="`/projects/${projectId}/evidences`">证据中心</el-menu-item>
          <el-menu-item :index="`/projects/${projectId}/review`">识别复核</el-menu-item>
          <el-menu-item :index="`/projects/${projectId}/records`">测评记录</el-menu-item>
          <el-menu-item :index="`/projects/${projectId}/exports`">导出中心</el-menu-item>
        </el-menu>
      </template>

      <div class="workspace-shell__aside-foot">
        <div class="workspace-shell__aside-caption">流程闭环</div>
        <div class="workspace-shell__aside-text">项目建档 → 证据采集 → OCR → 字段复核 → 记录复核 → 项目导出</div>
      </div>
    </el-aside>

    <el-container>
      <el-header class="workspace-shell__header">
        <div>
          <div class="workspace-shell__eyebrow">专业 · 清晰 · 可交付</div>
          <div class="workspace-shell__title">{{ title }}</div>
          <div class="workspace-shell__subtitle">{{ resolvedSubtitle }}</div>
        </div>
        <slot name="header-extra" />
      </el-header>

      <div v-if="currentProject" class="workspace-shell__project-bar">
        <div class="workspace-shell__project-main">
          <div class="workspace-shell__project-name">{{ currentProject.name }}</div>
          <div class="workspace-shell__project-meta">
            <span>项目编码：{{ currentProject.code || '未设置' }}</span>
            <span>项目类型：{{ currentProject.project_type }}</span>
          </div>
        </div>
        <div class="workspace-shell__project-tags">
          <AppStatusTag kind="project" :status="currentProject.status" />
          <el-tag type="info" effect="plain" round>当前项目</el-tag>
        </div>
      </div>

      <el-main class="workspace-shell__main">
        <div class="workspace-shell__content">
          <slot />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import AppStatusTag from '@/components/AppStatusTag.vue'
import { getProject } from '@/api/projects'
import { useAppStore } from '@/stores/app'

const props = defineProps<{
  title: string
  subtitle?: string
  projectId?: string
}>()

const route = useRoute()
const appStore = useAppStore()
const { currentProject } = storeToRefs(appStore)

const resolvedSubtitle = computed(() => props.subtitle || '以工作台方式串联测评流程、状态与交付闭环。')
const projectId = computed(() => props.projectId || (typeof route.params.projectId === 'string' ? route.params.projectId : ''))

const activeMenu = computed(() => {
  const currentPath = route.path
  const candidates = [
    '/dashboard',
    '/projects',
    '/template-rules',
    projectId.value ? `/projects/${projectId.value}/exports` : '',
    projectId.value ? `/projects/${projectId.value}/records` : '',
    projectId.value ? `/projects/${projectId.value}/review` : '',
    projectId.value ? `/projects/${projectId.value}/evidences` : '',
    projectId.value ? `/projects/${projectId.value}/assets` : '',
    projectId.value ? `/projects/${projectId.value}` : '',
  ].filter(Boolean)

  return candidates.find((item) => currentPath === item || currentPath.startsWith(`${item}/`)) || currentPath
})

watch(
  projectId,
  async (value) => {
    if (!value) {
      appStore.setCurrentProject(null)
      return
    }

    if (currentProject.value?.id === value) {
      return
    }

    try {
      const { data } = await getProject(value)
      appStore.setCurrentProject(data)
    } catch {
      appStore.setCurrentProject(null)
    }
  },
  { immediate: true },
)
</script>

<style scoped>
.workspace-shell {
  min-height: 100vh;
  background: #f3f6fb;
}

.workspace-shell__aside {
  display: flex;
  flex-direction: column;
  padding: 20px 16px;
  background: linear-gradient(180deg, #0f172a 0%, #111c34 100%);
  color: #e5eefb;
  border-right: 1px solid rgba(148, 163, 184, 0.12);
}

.workspace-shell__brand {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px 8px 24px;
}

.workspace-shell__brand-mark {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: linear-gradient(135deg, #2563eb, #14b8a6);
  color: #eff6ff;
  font-weight: 800;
}

.workspace-shell__brand-title {
  font-size: 16px;
  font-weight: 700;
  color: #f8fafc;
}

.workspace-shell__brand-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #94a3b8;
}

.workspace-shell__menu-title {
  margin: 10px 8px 8px;
  font-size: 12px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.workspace-shell__menu {
  border-right: none;
  background: transparent;
}

:deep(.workspace-shell__menu .el-menu-item) {
  margin-bottom: 6px;
  border-radius: 12px;
  color: #cbd5e1;
}

:deep(.workspace-shell__menu .el-menu-item.is-active) {
  background: rgba(37, 99, 235, 0.16);
  color: #eff6ff;
}

:deep(.workspace-shell__menu .el-menu-item:hover) {
  background: rgba(148, 163, 184, 0.12);
}

.workspace-shell__menu--project {
  margin-bottom: auto;
}

.workspace-shell__aside-foot {
  margin-top: 20px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.workspace-shell__aside-caption {
  font-size: 12px;
  color: #93c5fd;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.workspace-shell__aside-text {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.7;
  color: #cbd5e1;
}

.workspace-shell__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 28px 18px;
  height: auto;
  background: #f3f6fb;
}

.workspace-shell__eyebrow {
  font-size: 12px;
  font-weight: 700;
  color: #2563eb;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.workspace-shell__title {
  margin-top: 6px;
  font-size: 28px;
  font-weight: 800;
  color: #111827;
}

.workspace-shell__subtitle {
  margin-top: 6px;
  font-size: 14px;
  color: #64748b;
}

.workspace-shell__project-bar {
  margin: 0 28px;
  padding: 18px 20px;
  border-radius: 20px;
  background: linear-gradient(135deg, #ffffff, #f8fbff);
  border: 1px solid #dbe5f3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.workspace-shell__project-name {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.workspace-shell__project-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-top: 8px;
  color: #64748b;
  font-size: 13px;
}

.workspace-shell__project-tags {
  display: flex;
  align-items: center;
  gap: 10px;
}

.workspace-shell__main {
  padding: 20px 28px 28px;
  background: #f3f6fb;
}

.workspace-shell__content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

@media (max-width: 1200px) {
  .workspace-shell__project-bar {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
