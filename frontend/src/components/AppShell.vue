<template>
  <el-container class="workspace-shell">
    <el-aside width="272px" class="workspace-shell__aside">
      <div class="workspace-shell__brand">
        <div class="workspace-shell__brand-mark">DP</div>
        <div>
          <div class="workspace-shell__brand-title">等级保护测评工作台</div>
          <div class="workspace-shell__brand-subtitle">Security Assessment Workspace</div>
        </div>
      </div>

      <div class="workspace-shell__nav-block">
        <div class="workspace-shell__menu-title">全局导航</div>
        <el-menu :default-active="activeMenu" router class="workspace-shell__menu">
          <el-menu-item index="/dashboard">工作台 Dashboard</el-menu-item>
          <el-menu-item index="/projects">项目列表</el-menu-item>
          <el-menu-item index="/history-records">历史记录库</el-menu-item>
          <el-menu-item index="/guidance">指导书管理</el-menu-item>
          <el-menu-item index="/template-rules">模板规则</el-menu-item>
        </el-menu>
      </div>

      <div v-if="projectId" class="workspace-shell__nav-block workspace-shell__nav-block--stretch">
        <div class="workspace-shell__menu-title">项目工作区</div>
        <el-menu :default-active="activeMenu" router class="workspace-shell__menu workspace-shell__menu--project">
          <el-menu-item :index="`/projects/${projectId}`">项目详情</el-menu-item>
          <el-menu-item :index="`/projects/${projectId}/assets`">设备资产</el-menu-item>
          <el-menu-item :index="`/projects/${projectId}/evidences`">证据中心</el-menu-item>
          <el-menu-item :index="`/projects/${projectId}/review`">识别复核</el-menu-item>
          <el-menu-item :index="`/projects/${projectId}/records`">测评记录</el-menu-item>
          <el-menu-item :index="`/projects/${projectId}/exports`">导出中心</el-menu-item>
        </el-menu>
      </div>

      <div class="workspace-shell__aside-foot">
        <div class="workspace-shell__aside-caption">闭环路径</div>
        <div class="workspace-shell__aside-title">项目建档 → 证据采集 → OCR → 字段复核 → 记录复核 → 项目导出</div>
        <div class="workspace-shell__aside-text">以项目为抓手，把采集、识别、审校、导出拉通成一个可交付的测评工作台。</div>
      </div>
    </el-aside>

    <el-container>
      <el-header class="workspace-shell__header">
        <div class="workspace-shell__header-main">
          <div class="workspace-shell__eyebrow">专业 · 清晰 · 可交付</div>
          <div class="workspace-shell__title">{{ title }}</div>
          <div class="workspace-shell__subtitle">{{ resolvedSubtitle }}</div>
        </div>
        <div class="workspace-shell__header-extra">
          <slot name="header-extra" />
        </div>
      </el-header>

      <div v-if="currentProject" class="workspace-shell__project-bar">
        <div class="workspace-shell__project-main">
          <div class="workspace-shell__project-head">
            <div>
              <div class="workspace-shell__project-label">当前项目</div>
              <div class="workspace-shell__project-name">{{ currentProject.name }}</div>
            </div>
            <div class="workspace-shell__project-tags">
              <AppStatusTag kind="project" :status="currentProject.status" />
              <el-tag type="info" effect="plain" round>项目上下文已对齐</el-tag>
            </div>
          </div>
          <div class="workspace-shell__project-meta">
            <span>项目编码：{{ currentProject.code || '未设置' }}</span>
            <span>项目类型：{{ currentProject.project_type }}</span>
            <span>最近更新：{{ currentProject.updated_at || '-' }}</span>
          </div>
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
    '/history-records',
    '/guidance',
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
  background: var(--workspace-bg);
}

.workspace-shell__aside {
  display: flex;
  flex-direction: column;
  padding: 22px 16px 18px;
  background: linear-gradient(180deg, var(--workspace-sidebar) 0%, var(--workspace-sidebar-soft) 100%);
  color: #dbe7f7;
  border-right: 1px solid var(--workspace-sidebar-border);
}

.workspace-shell__brand {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px 8px 24px;
}

.workspace-shell__brand-mark {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: linear-gradient(135deg, #2563eb, #14b8a6);
  color: #eff6ff;
  font-weight: 800;
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.22);
}

.workspace-shell__brand-title {
  font-size: 16px;
  font-weight: 800;
  color: #f8fafc;
}

.workspace-shell__brand-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #8ea3c3;
}

.workspace-shell__nav-block {
  margin-bottom: 18px;
}

.workspace-shell__nav-block--stretch {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.workspace-shell__menu-title {
  margin: 0 8px 10px;
  font-size: 12px;
  color: #7f93b2;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700;
}

.workspace-shell__menu {
  border-right: none;
  background: transparent;
}

:deep(.workspace-shell__menu .el-menu-item) {
  height: 44px;
  margin-bottom: 6px;
  border-radius: 12px;
  color: #d3deee;
}

:deep(.workspace-shell__menu .el-menu-item.is-active) {
  background: rgba(37, 99, 235, 0.2);
  color: #eff6ff;
}

:deep(.workspace-shell__menu .el-menu-item:hover) {
  background: rgba(148, 163, 184, 0.12);
}

.workspace-shell__menu--project {
  margin-bottom: auto;
}

.workspace-shell__aside-foot {
  padding: 18px;
  border-radius: 20px;
  background: rgba(8, 15, 28, 0.42);
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.workspace-shell__aside-caption {
  font-size: 12px;
  color: #8fc7ff;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700;
}

.workspace-shell__aside-title {
  margin-top: 10px;
  line-height: 1.7;
  font-weight: 700;
  color: #f8fbff;
}

.workspace-shell__aside-text {
  margin-top: 10px;
  line-height: 1.7;
  color: #b8c7db;
  font-size: 13px;
}

.workspace-shell__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 28px 32px 18px;
  height: auto;
  background: transparent;
}

.workspace-shell__header-main {
  max-width: 760px;
}

.workspace-shell__header-extra {
  display: flex;
  align-items: center;
  gap: 12px;
}

.workspace-shell__eyebrow {
  font-size: 12px;
  font-weight: 800;
  color: var(--workspace-primary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.workspace-shell__title {
  margin-top: 8px;
  font-size: 30px;
  line-height: 1.15;
  font-weight: 800;
  color: var(--workspace-text);
}

.workspace-shell__subtitle {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--workspace-text-muted);
}

.workspace-shell__project-bar {
  margin: 0 32px;
  padding: 20px 22px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(237, 245, 255, 0.96));
  border: 1px solid rgba(37, 99, 235, 0.14);
  box-shadow: var(--workspace-shadow-soft);
}

.workspace-shell__project-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.workspace-shell__project-label {
  font-size: 12px;
  color: var(--workspace-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700;
}

.workspace-shell__project-name {
  margin-top: 8px;
  font-size: 20px;
  font-weight: 800;
  color: var(--workspace-text);
}

.workspace-shell__project-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-top: 12px;
  color: var(--workspace-text-secondary);
  font-size: 13px;
}

.workspace-shell__project-tags {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.workspace-shell__main {
  padding: 20px 32px 32px;
  background: transparent;
}

.workspace-shell__content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

@media (max-width: 1280px) {
  .workspace-shell__header,
  .workspace-shell__project-head {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 960px) {
  .workspace-shell {
    display: block;
  }

  .workspace-shell__aside {
    width: 100%;
  }

  .workspace-shell__header,
  .workspace-shell__project-bar,
  .workspace-shell__main {
    margin: 0;
    padding-inline: 20px;
  }
}
</style>
