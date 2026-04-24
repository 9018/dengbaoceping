import apiClient, { unwrapResponse } from './http'
import type { Asset, AssetPayload } from '@/types/domain'

export async function listAssets(projectId: string) {
  return unwrapResponse<Asset[]>(apiClient.get(`/projects/${projectId}/assets`))
}

export async function getAsset(assetId: string) {
  return unwrapResponse<Asset>(apiClient.get(`/assets/${assetId}`))
}

export async function createAsset(projectId: string, payload: AssetPayload) {
  return unwrapResponse<Asset>(apiClient.post(`/projects/${projectId}/assets`, payload))
}

export async function updateAsset(assetId: string, payload: Partial<AssetPayload>) {
  return unwrapResponse<Asset>(apiClient.put(`/assets/${assetId}`, payload))
}

export async function deleteAsset(assetId: string) {
  return unwrapResponse<null>(apiClient.delete(`/assets/${assetId}`))
}
