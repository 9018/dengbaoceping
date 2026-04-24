import apiClient, { unwrapResponse } from './http'
import type { Project, ProjectPayload } from '@/types/domain'

export async function listProjects() {
  return unwrapResponse<Project[]>(apiClient.get('/projects'))
}

export async function getProject(projectId: string) {
  return unwrapResponse<Project>(apiClient.get(`/projects/${projectId}`))
}

export async function createProject(payload: ProjectPayload) {
  return unwrapResponse<Project>(apiClient.post('/projects', payload))
}

export async function updateProject(projectId: string, payload: Partial<ProjectPayload>) {
  return unwrapResponse<Project>(apiClient.put(`/projects/${projectId}`, payload))
}

export async function deleteProject(projectId: string) {
  return unwrapResponse<null>(apiClient.delete(`/projects/${projectId}`))
}
