import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listProjects } from '@/api/projects'
import type { Project } from '@/types/domain'

export const useProjectsStore = defineStore('projects', () => {
  const projects = ref<Project[]>([])

  async function refreshProjects() {
    const { data } = await listProjects()
    projects.value = data
    return data
  }

  function setProjects(items: Project[]) {
    projects.value = items
  }

  return {
    projects,
    refreshProjects,
    setProjects,
  }
})
