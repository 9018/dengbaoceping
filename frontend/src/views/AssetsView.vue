<template>
  <AppShell :project-id="projectId" title="设备资产页" subtitle="面向测评项目统一维护资产台账、来源、路径和入库状态。">
    <div class="page-stack">
      <StatsCards :items="summaryCards" />

      <el-card>
        <template #header>
          <div class="toolbar">
            <div>
              <div class="section-title">设备资产列表</div>
              <div class="section-subtitle">统一维护设备名称、分类、路径和入库状态。</div>
            </div>
            <el-space>
              <el-button @click="loadAssets">刷新</el-button>
              <el-button type="primary" @click="openCreate">新增设备</el-button>
            </el-space>
          </div>
        </template>

        <el-form inline class="filter-bar">
          <el-form-item label="状态">
            <el-select v-model="statusFilter" clearable placeholder="全部状态" style="width: 180px">
              <el-option v-for="status in assetStatusOptions" :key="status" :label="getStatusLabel('asset', status)" :value="status" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input v-model="keyword" clearable placeholder="搜索设备名称、分类、来源" style="width: 280px" />
          </el-form-item>
        </el-form>

        <el-table :data="filteredAssets" border>
          <el-table-column prop="filename" label="设备名称/文件名" min-width="180" />
          <el-table-column prop="category_label" label="分类" min-width="140" />
          <el-table-column prop="relative_path" label="相对路径" min-width="220" show-overflow-tooltip />
          <el-table-column label="状态" width="120">
            <template #default="scope">
              <AppStatusTag kind="asset" :status="scope.row.ingest_status" />
            </template>
          </el-table-column>
          <el-table-column prop="source" label="来源" width="140" />
          <el-table-column prop="updated_at" label="更新时间" min-width="180" />
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
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import AppStatusTag from '@/components/AppStatusTag.vue'
import AssetFormDialog from '@/components/AssetFormDialog.vue'
import StatsCards, { type StatsCardItem } from '@/components/StatsCards.vue'
import { createAsset, deleteAsset, listAssets, updateAsset } from '@/api/assets'
import { assetStatusOptions } from '@/utils/constants'
import { getStatusLabel } from '@/utils/status'
import type { Asset } from '@/types/domain'

const props = defineProps<{ projectId: string }>()
const assets = ref<Asset[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingAsset = ref<Asset | null>(null)
const statusFilter = ref('')
const keyword = ref('')

const summaryCards = computed<StatsCardItem[]>(() => [
  { label: '资产总数', value: assets.value.length, tip: '项目内全部设备资产', tone: 'primary' },
  { label: '待处理', value: assets.value.filter((item) => item.ingest_status === 'pending').length, tip: '待补充或待入库', tone: 'warning' },
  { label: '已入库', value: assets.value.filter((item) => item.ingest_status === 'processed').length, tip: '已完成整理', tone: 'success' },
  { label: '失败', value: assets.value.filter((item) => item.ingest_status === 'failed').length, tip: '需要排查', tone: 'default' },
])

const filteredAssets = computed(() => {
  const search = keyword.value.trim().toLowerCase()
  return assets.value.filter((item) => {
    const matchStatus = !statusFilter.value || item.ingest_status === statusFilter.value
    const matchKeyword =
      !search ||
      [item.filename, item.category_label, item.source]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(search))
    return matchStatus && matchKeyword
  })
})

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
  gap: 12px;
}

.filter-bar {
  margin-bottom: 16px;
}
</style>
