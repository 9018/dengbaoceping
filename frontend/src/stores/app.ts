import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { Project } from '@/types/domain'

export const useAppStore = defineStore('app', () => {
  const loading = ref(false)
  const currentProject = ref<Project | null>(null)

  const currentProjectName = computed(() => currentProject.value?.name || '未选择项目')

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setCurrentProject(project: Project | null) {
    currentProject.value = project
  }

  return {
    loading,
    currentProject,
    currentProjectName,
    setLoading,
    setCurrentProject,
  }
})
