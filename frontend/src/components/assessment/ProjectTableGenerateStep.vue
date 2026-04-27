<template>
  <WorkflowStepCard title="生成项目测评表" summary="按资产类型复制主模板项，形成项目内待填写测评表。">
    <div class="step-stack">
      <el-select :model-value="selectedAssetId" placeholder="选择资产" style="width: 320px" @change="$emit('selectAsset', $event)">
        <el-option v-for="asset in assets" :key="asset.id" :label="asset.filename" :value="asset.id" />
      </el-select>
      <el-space wrap>
        <el-button type="primary" :disabled="!selectedAssetId" @click="$emit('generate')">生成测评表</el-button>
        <el-button @click="$emit('refresh')">刷新测评表</el-button>
      </el-space>

      <div v-if="currentTable" class="table-summary-grid">
        <div class="soft-panel">
          <div class="panel-label">当前测评表</div>
          <div class="panel-value">{{ currentTable.name }}</div>
          <div class="panel-meta">条目数：{{ currentTable.item_count }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">状态</div>
          <div class="panel-value">
            <AppStatusTag kind="project" :status="currentTable.status" />
          </div>
          <div class="panel-meta">资产：{{ currentAsset?.filename || '-' }}</div>
        </div>
      </div>

      <el-alert
        v-if="conflictMessage"
        :title="conflictMessage"
        type="warning"
        show-icon
        :closable="false"
      />

      <el-table :data="tables" border>
        <el-table-column prop="name" label="测评表名称" min-width="220" />
        <el-table-column label="状态" width="140">
          <template #default="scope">
            <AppStatusTag kind="project" :status="scope.row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="item_count" label="条目数" width="120" />
        <el-table-column label="操作" min-width="320" fixed="right">
          <template #default="scope">
            <el-space wrap>
              <el-button size="small" @click="$emit('selectTable', scope.row.id)">查看条目</el-button>
              <el-button size="small" @click="$emit('renameTable', scope.row)">重命名</el-button>
              <el-button size="small" :type="selectedAssetId === scope.row.asset_id ? 'warning' : 'primary'" @click="$emit('regenerateForAsset', scope.row)">
                重新生成
              </el-button>
              <el-popconfirm title="确认删除该项目测评表？" @confirm="$emit('deleteTable', scope.row)">
                <template #reference>
                  <el-button size="small" type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </el-space>
          </template>
        </el-table-column>
      </el-table>

      <el-card v-if="currentTable" shadow="never">
        <template #header>
          <div class="section-header">
            <div>
              <div class="section-title">当前测评项预览</div>
              <div class="section-subtitle">优先暴露真实测评项，便于确认生成结果、继续匹配和处理冲突。</div>
            </div>
          </div>
        </template>
        <el-table :data="items" border>
          <el-table-column label="当前" width="90">
            <template #default="scope">
              <el-tag v-if="scope.row.id === currentItemId" type="success" effect="light">当前项</el-tag>
              <el-button v-else size="small" @click="$emit('selectItem', scope.row.id)">设为当前</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="sheet_name" label="工作表" width="140" />
          <el-table-column prop="row_index" label="行号" width="90" />
          <el-table-column prop="item_code" label="条目编码" width="150" />
          <el-table-column prop="control_point" label="控制点" min-width="180" show-overflow-tooltip />
          <el-table-column prop="item_text" label="测评项" min-width="220" show-overflow-tooltip />
          <el-table-column label="状态" width="140">
            <template #default="scope">
              <span>{{ scope.row.status || 'draft' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="260" fixed="right">
            <template #default="scope">
              <el-space wrap>
                <el-button size="small" @click="$emit('editItem', scope.row)">编辑</el-button>
                <el-popconfirm title="确认删除该测评项？" @confirm="$emit('deleteItem', scope.row)">
                  <template #reference>
                    <el-button size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </WorkflowStepCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppStatusTag from '@/components/AppStatusTag.vue'
import WorkflowStepCard from '@/components/workflow/WorkflowStepCard.vue'
import type { Asset, ProjectAssessmentItem, ProjectAssessmentTable } from '@/types/domain'

const props = defineProps<{
  assets: Asset[]
  tables: ProjectAssessmentTable[]
  items: ProjectAssessmentItem[]
  selectedAssetId: string
  currentTableId: string
  currentItemId: string
  conflictMessage?: string
}>()

const currentTable = computed(() => props.tables.find((item) => item.id === props.currentTableId) || null)
const currentAsset = computed(() => props.assets.find((item) => item.id === currentTable.value?.asset_id) || null)

defineEmits<{
  selectAsset: [value: string]
  generate: []
  refresh: []
  selectTable: [tableId: string]
  renameTable: [table: ProjectAssessmentTable]
  regenerateForAsset: [table: ProjectAssessmentTable]
  deleteTable: [table: ProjectAssessmentTable]
  selectItem: [itemId: string]
  editItem: [item: ProjectAssessmentItem]
  deleteItem: [item: ProjectAssessmentItem]
}>()
</script>

<style scoped>
.step-stack { display: flex; flex-direction: column; gap: 12px; }
.table-summary-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }

@media (max-width: 768px) {
  .table-summary-grid { grid-template-columns: 1fr; }
}
</style>
