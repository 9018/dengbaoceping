<template>
  <AppShell :project-id="projectId" title="设备管理" subtitle="新增、编辑、删除设备资产并展示设备列表">
    <el-card>
      <template #header>
        <div class="toolbar">
          <span>设备资产列表</span>
          <el-space>
            <el-button @click="loadAssets">刷新</el-button>
            <el-button type="primary" @click="openCreate">新增设备</el-button>
          </el-space>
        </div>
      </template>
      <el-table :data="assets" border>
        <el-table-column prop="filename" label="设备名称/文件名" min-width="180" />
        <el-table-column prop="category_label" label="分类" min-width="140" />
        <el-table-column prop="relative_path" label="相对路径" min-width="180" show-overflow-tooltip />
        <el-table-column prop="ingest_status" label="状态" width="120" />
        <el-table-column prop="source" label="来源" width="120" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-space>
              <el-button size="small" @click="openEdit(scope.row)">编辑</el-button>
              <el-popconfirm title="确认删除该设备资产？" @confirm="removeAsset(scope.row.id)">
                <template #reference>
                  <el-button size="small" type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <AssetFormDialog v-model="dialogVisible" :asset="editingAsset" :mode="dialogMode" @submit="submitAsset" />
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import AssetFormDialog from '@/components/AssetFormDialog.vue'
import { createAsset, deleteAsset, listAssets, updateAsset } from '@/api/assets'
import type { Asset } from '@/types/domain'

const props = defineProps<{ projectId: string }>()
const assets = ref<Asset[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingAsset = ref<Asset | null>(null)

async function loadAssets() {
  const { data } = await listAssets(props.projectId)
  assets.value = data
}

function openCreate() {
  dialogMode.value = 'create'
  editingAsset.value = null
  dialogVisible.value = true
}

function openEdit(asset: Asset) {
  dialogMode.value = 'edit'
  editingAsset.value = asset
  dialogVisible.value = true
}

async function submitAsset(payload: Record<string, unknown>) {
  if (dialogMode.value === 'create') {
    await createAsset(props.projectId, payload as never)
    ElMessage.success('设备资产创建成功')
  } else if (editingAsset.value) {
    await updateAsset(editingAsset.value.id, payload)
    ElMessage.success('设备资产更新成功')
  }
  dialogVisible.value = false
  await loadAssets()
}

async function removeAsset(assetId: string) {
  await deleteAsset(assetId)
  ElMessage.success('设备资产已删除')
  await loadAssets()
}

onMounted(loadAssets)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
