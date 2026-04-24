<template>
  <el-container class="app-shell">
    <el-aside width="220px" class="app-shell__aside">
      <div class="app-shell__brand">CPGJ 工具页</div>
      <el-menu :default-active="activeMenu" router class="app-shell__menu">
        <el-menu-item index="/projects">项目列表</el-menu-item>
        <el-menu-item v-if="projectId" :index="`/projects/${projectId}`">项目详情</el-menu-item>
        <el-menu-item v-if="projectId" :index="`/projects/${projectId}/assets`">设备管理</el-menu-item>
        <el-menu-item v-if="projectId" :index="`/projects/${projectId}/evidences`">证据管理</el-menu-item>
        <el-menu-item v-if="projectId" :index="`/projects/${projectId}/review`">识别复核</el-menu-item>
        <el-menu-item v-if="projectId" :index="`/projects/${projectId}/records`">记录中心</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-shell__header">
        <div>
          <div class="app-shell__title">{{ title }}</div>
          <div class="app-shell__subtitle">{{ subtitle }}</div>
        </div>
        <el-tag type="info">当前项目：{{ currentProjectName }}</el-tag>
      </el-header>
      <el-main class="app-shell__main">
        <slot />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAppStore } from '@/stores/app'

const props = defineProps<{
  title: string
  subtitle?: string
  projectId?: string
}>()

const route = useRoute()
const appStore = useAppStore()
const { currentProjectName } = storeToRefs(appStore)

const activeMenu = computed(() => route.path)
const subtitle = computed(() => props.subtitle || '先保证工具可用，接口路径严格对齐后端')
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.app-shell__aside {
  background: #001529;
  color: #fff;
}

.app-shell__brand {
  padding: 20px 16px;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.app-shell__menu {
  border-right: none;
}

.app-shell__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}

.app-shell__title {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
}

.app-shell__subtitle {
  margin-top: 4px;
  color: #909399;
  font-size: 13px;
}

.app-shell__main {
  background: #f5f7fa;
}
</style>
