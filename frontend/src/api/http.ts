import axios, { AxiosError } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse } from '@/types/domain'

export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() || '/api/v1'

const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000,
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiResponse<unknown>>) => {
    const message = error.response?.data?.error?.message || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  },
)

export async function unwrapResponse<T>(promise: Promise<{ data: ApiResponse<T> }>): Promise<{ data: T; message?: string; meta?: ApiResponse<T>['meta'] }> {
  const response = await promise
  const payload = response.data
  if (!payload.success) {
    const message = payload.error?.message || '请求失败'
    ElMessage.error(message)
    throw new Error(message)
  }
  return {
    data: payload.data,
    message: payload.message,
    meta: payload.meta,
  }
}

export default apiClient
