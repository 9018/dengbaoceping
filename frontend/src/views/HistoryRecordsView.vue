<template>
  <AppShell title="历史测评记录库" subtitle="最终测评记录 Excel 结构化导入，形成可检索、可仿写、可匹配的历史人工样本库。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">History Library</div>
            <div class="section-title">历史测评记录库</div>
            <div class="section-subtitle">逐 Sheet、逐行解析最终人工测评记录，沉淀资产信息、测评项、结果记录和符合情况。</div>
          </div>
          <el-space wrap>
            <el-button @click="loadAll">刷新</el-button>
            <el-upload :auto-upload="false" :show-file-list="false" accept=".xlsx" :on-change="handleFileChange">
              <el-button type="primary" :loading="importing">上传 Excel</el-button>
            </el-upload>
          </el-space>
        </div>
        <StatsCards :items="summaryCards" />
      </section>

      <section class="page-grid-3" v-if="lastImport">
        <div class="soft-panel">
          <div class="panel-label">最近导入文件</div>
          <div class="panel-value panel-value--path">{{ lastImport.source_file }}</div>
          <div class="panel-meta">工作表数量：{{ lastImport.sheet_count }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">导入记录数</div>
          <div class="panel-value">{{ lastImport.imported_count }}</div>
          <div class="panel-meta">跳过行数：{{ lastImport.skipped_count }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">符合情况分布</div>
          <div class="panel-meta panel-meta--list">
            <div v-for="(total, key) in lastImport.compliance_status_counts" :key="key">{{ key }}：{{ total }}</div>
          </div>
        </div>
      </section>

      <el-card>
        <template #header>
          <div class="section-header">
            <div>
              <div class="section-title">历史库管理</div>
              <div class="section-subtitle">统一查看记录列表、字段值、重复记录，并处理批量治理动作。</div>
            </div>
            <el-tag type="info">重复组 {{ summary.duplicate_group_count }}</el-tag>
          </div>
        </template>

        <el-tabs v-model="activeTab">
          <el-tab-pane label="记录列表" name="records">
            <div class="page-filter-bar">
              <el-form inline @submit.prevent>
                <el-form-item label="资产">
                  <el-input v-model="filters.asset_name" clearable placeholder="输入资产名称" style="width: 180px" />
                </el-form-item>
                <el-form-item label="Sheet">
                  <el-select v-model="filters.sheet_name" clearable filterable placeholder="全部工作表" style="width: 220px">
                    <el-option v-for="item in sheetOptions" :key="item" :label="item" :value="item" />
                  </el-select>
                </el-form-item>
                <el-form-item label="控制点">
                  <el-input v-model="filters.control_point" clearable placeholder="输入控制点关键词" style="width: 220px" />
                </el-form-item>
                <el-form-item label="符合情况">
                  <el-select v-model="filters.compliance_result" clearable placeholder="全部状态" style="width: 180px">
                    <el-option v-for="item in complianceOptions" :key="item" :label="item" :value="item" />
                  </el-select>
                </el-form-item>
                <el-form-item label="资产类型">
                  <el-select v-model="filters.asset_type" clearable placeholder="全部类型" style="width: 180px">
                    <el-option v-for="item in assetTypeOptions" :key="item" :label="item" :value="item" />
                  </el-select>
                </el-form-item>
                <el-form-item label="关键词">
                  <el-input v-model="keyword" clearable placeholder="搜索结果记录/测评项/关键词" style="width: 240px" @keyup.enter="loadRecords" />
                </el-form-item>
                <el-form-item>
                  <el-space>
                    <el-button type="primary" @click="loadRecords">查询</el-button>
                    <el-button @click="resetFilters">重置</el-button>
                  </el-space>
                </el-form-item>
              </el-form>
            </div>

            <el-table :data="rows" border v-loading="loading">
              <el-table-column prop="asset_name" label="资产" min-width="160" show-overflow-tooltip />
              <el-table-column prop="sheet_name" label="Sheet" min-width="150" />
              <el-table-column prop="asset_ip" label="IP" width="140" />
              <el-table-column prop="asset_type" label="资产类型" width="110" />
              <el-table-column prop="control_point" label="控制点" min-width="180" show-overflow-tooltip />
              <el-table-column prop="item_text" label="测评项" min-width="220" show-overflow-tooltip />
              <el-table-column prop="compliance_result" label="符合情况" width="120" />
              <el-table-column prop="score_weight" label="权重" width="90" />
              <el-table-column prop="item_code" label="编号" width="110" />
              <el-table-column label="关键词" min-width="220">
                <template #default="scope">
                  <div class="tag-group">
                    <el-tag v-for="item in scope.row.keywords_json.slice(0, 6)" :key="item" size="small" effect="plain">{{ item }}</el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="scope">
                  <el-button size="small" type="primary" @click="openDetail(scope.row.id)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="table-footer">
              <div class="muted-text">共 {{ total }} 条记录</div>
              <el-pagination
                background
                layout="total, prev, pager, next, sizes"
                :total="total"
                :current-page="page"
                :page-size="pageSize"
                :page-sizes="[20, 50, 100, 200]"
                @current-change="handlePageChange"
                @size-change="handlePageSizeChange"
              />
            </div>
          </el-tab-pane>

          <el-tab-pane label="工作表管理" name="sheets">
            <FieldValueManager
              title="工作表值管理"
              field-name="sheet_name"
              :rows="sheetValues"
              @rename="handleRenameFieldValue"
              @delete="handleDeleteFieldValue"
            />
          </el-tab-pane>

          <el-tab-pane label="资产类型管理" name="asset_types">
            <FieldValueManager
              title="资产类型值管理"
              field-name="asset_type"
              :rows="assetTypeValues"
              @rename="handleRenameFieldValue"
              @delete="handleDeleteFieldValue"
            />
          </el-tab-pane>

          <el-tab-pane label="符合状态管理" name="compliance">
            <FieldValueManager
              title="符合情况值管理"
              field-name="compliance_result"
              :rows="complianceValues"
              @rename="handleRenameFieldValue"
              @delete="handleDeleteFieldValue"
            />
          </el-tab-pane>

          <el-tab-pane label="重复记录处理" name="duplicates">
            <div class="page-stack">
              <div class="toolbar-row">
                <div class="muted-text">共 {{ duplicateGroups.length }} 个重复组，重复记录 {{ summary.duplicate_record_count }} 条</div>
                <el-button type="danger" plain @click="handleDeleteDuplicates">按 keep_first 清理重复</el-button>
              </div>
              <el-table :data="duplicateGroups" border>
                <el-table-column prop="sheet_name" label="Sheet" min-width="140" />
                <el-table-column prop="asset_name" label="资产" min-width="140" />
                <el-table-column prop="asset_type" label="资产类型" width="120" />
                <el-table-column prop="control_point" label="控制点" min-width="180" show-overflow-tooltip />
                <el-table-column prop="duplicate_count" label="重复条数" width="100" />
                <el-table-column prop="source_file_count" label="来源文件数" width="110" />
                <el-table-column label="重复记录" min-width="360">
                  <template #default="scope">
                    <div class="duplicate-records">
                      <div v-for="item in scope.row.records" :key="item.id" class="duplicate-record-item">
                        <span>{{ item.item_code || item.item_no || item.id }}</span>
                        <span>{{ item.source_file }}</span>
                        <span>{{ item.compliance_result || item.compliance_status || '-' }}</span>
                      </div>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <div class="page-grid-2">
        <el-card>
          <template #header>
            <div class="section-header">
              <div class="section-title">相似样本</div>
              <div class="section-subtitle">基于 OCR 文本、控制点、测评项、页面类型和资产类型的规则打分，返回最接近的历史记录。</div>
            </div>
          </template>
          <el-form label-width="88px" @submit.prevent>
            <el-form-item label="控制点">
              <el-input v-model="similarQuery.control_point" clearable placeholder="例如：边界访问控制" />
            </el-form-item>
            <el-form-item label="OCR文本">
              <el-input v-model="similarQuery.ocr_text" clearable type="textarea" :rows="2" placeholder="可粘贴 OCR 识别文本" />
            </el-form-item>
            <el-form-item label="页面类型">
              <el-input v-model="similarQuery.page_type" clearable placeholder="例如：日志审计 / 系统边界" />
            </el-form-item>
            <el-form-item label="测评项">
              <el-input v-model="similarQuery.item_text" clearable placeholder="例如：应限制非授权访问" />
            </el-form-item>
            <el-form-item label="资产类型">
              <el-select v-model="similarQuery.asset_type" clearable placeholder="可选">
                <el-option v-for="item in assetTypeOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadSimilar">获取相似记录</el-button>
            </el-form-item>
          </el-form>
          <el-table :data="similarRows" border>
            <el-table-column prop="sheet_name" label="Sheet" min-width="140" />
            <el-table-column prop="compliance_result" label="符合情况" width="120" />
            <el-table-column prop="score" label="得分" width="80" />
            <el-table-column label="命中原因" min-width="220" show-overflow-tooltip>
              <template #default="scope">{{ scope.row.reasons.join('；') }}</template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card>
          <template #header>
            <div class="section-header">
              <div class="section-title">句式统计</div>
              <div class="section-subtitle">按常见写法短语统计历史记录分布，辅助沉淀人工写法风格。</div>
            </div>
          </template>
          <el-table :data="phrases" border>
            <el-table-column prop="phrase" label="短语" width="120" />
            <el-table-column prop="total" label="命中次数" width="100" />
            <el-table-column label="状态分布" min-width="220">
              <template #default="scope">
                <div class="phrase-list">
                  <div v-for="(totalValue, key) in scope.row.compliance_status_counts" :key="key">{{ key }}：{{ totalValue }}</div>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <el-drawer v-model="detailVisible" title="历史记录详情" size="720px">
        <div v-if="detailItem" class="page-stack">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="项目名称">{{ detailItem.project_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="来源文件">{{ detailItem.source_file }}</el-descriptions-item>
            <el-descriptions-item label="Sheet">{{ detailItem.sheet_name }}</el-descriptions-item>
            <el-descriptions-item label="资产名称">{{ detailItem.asset_name }}</el-descriptions-item>
            <el-descriptions-item label="资产类型">{{ detailItem.asset_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="IP / 版本">{{ detailItem.asset_ip || '-' }} / {{ detailItem.asset_version || '-' }}</el-descriptions-item>
            <el-descriptions-item label="标准类型">{{ detailItem.standard_type || detailItem.extension_standard || '-' }}</el-descriptions-item>
            <el-descriptions-item label="控制点">{{ detailItem.control_point || '-' }}</el-descriptions-item>
            <el-descriptions-item label="测评项">{{ detailItem.item_text || detailItem.evaluation_item || '-' }}</el-descriptions-item>
            <el-descriptions-item label="符合情况">{{ detailItem.compliance_result || detailItem.compliance_status || '-' }}</el-descriptions-item>
            <el-descriptions-item label="编号 / 权重">{{ detailItem.item_code || detailItem.item_no || '-' }} / {{ detailItem.score_weight ?? detailItem.score ?? '-' }}</el-descriptions-item>
          </el-descriptions>

          <el-card>
            <template #header>
              <div class="section-header">
                <div class="section-title">结果记录</div>
                <div class="section-subtitle">保留人工原始写法，便于横向参考。</div>
              </div>
            </template>
            <div class="muted-text record-text">{{ detailItem.raw_text || detailItem.record_text || '暂无结果记录。' }}</div>
          </el-card>

          <el-card>
            <template #header>
              <div class="section-header">
                <div class="section-title">关键词</div>
                <div class="section-subtitle">规则抽取的检索关键词。</div>
              </div>
            </template>
            <div class="tag-group">
              <el-tag v-for="item in detailItem.keywords_json" :key="item" effect="plain">{{ item }}</el-tag>
            </div>
          </el-card>
        </div>
      </el-drawer>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import StatsCards, { type StatsCardItem } from '@/components/StatsCards.vue'
import {
  deleteHistoryDuplicateGroups,
  deleteHistoryRecordsByFieldValue,
  getHistoryDuplicateGroups,
  getHistoryPhrases,
  getHistoryRecord,
  getHistorySimilarRecords,
  getHistoryStats,
  getHistorySummary,
  importHistoryExcel,
  listHistoryFieldValues,
  listHistoryRecords,
  renameHistoryFieldValue,
} from '@/api/history'
import type {
  HistoryDuplicateGroup,
  HistoryFieldValue,
  HistoryImportResult,
  HistoryPhraseSummary,
  HistoryRecord,
  HistorySimilarRecord,
  HistoryStats,
  HistorySummary,
} from '@/types/domain'

const FieldValueManager = defineComponent({
  name: 'FieldValueManager',
  props: {
    title: { type: String, required: true },
    fieldName: { type: String, required: true },
    rows: { type: Array as () => HistoryFieldValue[], required: true },
  },
  emits: ['rename', 'delete'],
  setup(props, { emit }) {
    return () =>
      h('div', { class: 'page-stack' }, [
        h('div', { class: 'toolbar-row' }, [
          h('div', { class: 'muted-text' }, props.title),
          h('div', { class: 'muted-text' }, `共 ${props.rows.length} 个值`),
        ]),
        h(
          'div',
          props.rows.map((item) =>
            h('div', { class: 'field-value-row', key: `${props.fieldName}-${item.value}` }, [
              h('div', { class: 'field-value-main' }, [
                h('span', { class: 'field-value-name' }, item.value),
                h('span', { class: 'field-value-count' }, `${item.count} 条`),
              ]),
              h('div', { class: 'field-value-actions' }, [
                h(
                  'button',
                  {
                    class: 'link-button',
                    onClick: async () => {
                      const nextValue = window.prompt(`请输入 ${item.value} 的新值`, item.value)
                      if (nextValue && nextValue !== item.value) {
                        emit('rename', { fieldName: props.fieldName, fromValue: item.value, toValue: nextValue })
                      }
                    },
                  },
                  '重命名',
                ),
                h(
                  'button',
                  {
                    class: 'link-button link-button--danger',
                    onClick: () => emit('delete', { fieldName: props.fieldName, value: item.value }),
                  },
                  '删除',
                ),
              ]),
            ]),
          ),
        ),
      ])
  },
})

const loading = ref(false)
const importing = ref(false)
const detailVisible = ref(false)
const detailItem = ref<HistoryRecord | null>(null)
const rows = ref<HistoryRecord[]>([])
const phrases = ref<HistoryPhraseSummary[]>([])
const similarRows = ref<HistorySimilarRecord[]>([])
const duplicateGroups = ref<HistoryDuplicateGroup[]>([])
const sheetValues = ref<HistoryFieldValue[]>([])
const assetTypeValues = ref<HistoryFieldValue[]>([])
const complianceValues = ref<HistoryFieldValue[]>([])
const keyword = ref('')
const lastImport = ref<HistoryImportResult | null>(null)
const activeTab = ref('records')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const stats = ref<HistoryStats>({
  sheet_count: 0,
  total: 0,
  compliance_status_counts: {},
  asset_type_counts: {},
})
const summary = ref<HistorySummary>({
  total: 0,
  sheet_count: 0,
  source_file_count: 0,
  duplicate_group_count: 0,
  duplicate_record_count: 0,
  compliance_status_counts: {},
  asset_type_counts: {},
})
const filters = reactive({
  asset_name: '',
  sheet_name: '',
  control_point: '',
  compliance_result: '',
  asset_type: '',
})
const similarQuery = reactive({
  ocr_text: '',
  page_type: '',
  control_point: '',
  item_text: '',
  asset_type: '',
})

const summaryCards = computed<StatsCardItem[]>(() => [
  { label: '工作表数量', value: summary.value.sheet_count, tip: '已导入的 Sheet 数', tone: 'primary' },
  { label: '记录总数', value: summary.value.total, tip: '全部历史人工记录', tone: 'success' },
  { label: '来源文件', value: summary.value.source_file_count, tip: '已导入来源文件数', tone: 'default' },
  { label: '重复记录', value: summary.value.duplicate_record_count, tip: '待治理的重复历史记录', tone: 'warning' },
])

const sheetOptions = computed(() => sheetValues.value.map((item) => item.value))
const complianceOptions = computed(() => Object.keys(summary.value.compliance_status_counts))
const assetTypeOptions = computed(() => Object.keys(summary.value.asset_type_counts))

async function loadStats() {
  const { data } = await getHistoryStats()
  stats.value = data
}

async function loadSummary() {
  const { data } = await getHistorySummary()
  summary.value = data
}

async function loadPhrases() {
  const { data } = await getHistoryPhrases()
  phrases.value = data
}

async function loadRecords() {
  loading.value = true
  try {
    const { data } = await listHistoryRecords({
      asset_name: filters.asset_name || undefined,
      sheet_name: filters.sheet_name || undefined,
      control_point: filters.control_point || undefined,
      compliance_result: filters.compliance_result || undefined,
      asset_type: filters.asset_type || undefined,
      keyword: keyword.value.trim() || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadDuplicateGroups() {
  const { data } = await getHistoryDuplicateGroups()
  duplicateGroups.value = data
}

async function loadFieldValues() {
  const [sheetResp, assetResp, complianceResp] = await Promise.all([
    listHistoryFieldValues('sheet_name'),
    listHistoryFieldValues('asset_type'),
    listHistoryFieldValues('compliance_result'),
  ])
  sheetValues.value = sheetResp.data
  assetTypeValues.value = assetResp.data
  complianceValues.value = complianceResp.data
}

async function loadSimilar() {
  if (!similarQuery.ocr_text.trim() && !similarQuery.control_point.trim() && !similarQuery.item_text.trim() && !similarQuery.page_type.trim() && !similarQuery.asset_type) {
    ElMessage.warning('请先填写至少一个相似搜索条件')
    return
  }
  const { data } = await getHistorySimilarRecords({
    ocr_text: similarQuery.ocr_text.trim() || undefined,
    page_type: similarQuery.page_type.trim() || undefined,
    control_point: similarQuery.control_point.trim() || undefined,
    item_text: similarQuery.item_text.trim() || undefined,
    asset_type: similarQuery.asset_type || undefined,
  })
  similarRows.value = data
}

async function openDetail(recordId: string) {
  const { data } = await getHistoryRecord(recordId)
  detailItem.value = data
  detailVisible.value = true
}

async function handleFileChange(uploadFile: UploadFile) {
  const raw = uploadFile.raw
  if (!raw) return
  importing.value = true
  try {
    const { data, message } = await importHistoryExcel(raw)
    lastImport.value = data
    ElMessage.success(message || '历史记录 Excel 导入成功')
    await loadAll()
  } finally {
    importing.value = false
  }
}

async function handleRenameFieldValue(payload: { fieldName: string; fromValue: string; toValue: string }) {
  await renameHistoryFieldValue(payload.fieldName, {
    from_value: payload.fromValue,
    to_value: payload.toValue,
  })
  ElMessage.success('字段值更新成功')
  await loadAll()
}

async function handleDeleteFieldValue(payload: { fieldName: string; value: string }) {
  try {
    await ElMessageBox.confirm(`确认删除字段值 ${payload.value} 对应的历史记录吗？`, '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }

  try {
    await deleteHistoryRecordsByFieldValue(payload.fieldName, payload.value)
    ElMessage.success('字段值对应记录已删除')
  } catch (error) {
    const message = error instanceof Error ? error.message : ''
    if (!message.includes('引用')) {
      throw error
    }
    await ElMessageBox.confirm(`字段值 ${payload.value} 存在被引用记录，是否强制删除？`, '强制删除确认', {
      type: 'warning',
    })
    await deleteHistoryRecordsByFieldValue(payload.fieldName, payload.value, true)
    ElMessage.success('字段值对应记录已强制删除')
  }
  await loadAll()
}

async function handleDeleteDuplicates() {
  try {
    await ElMessageBox.confirm('确认按 keep_first 策略清理重复记录吗？', '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }

  try {
    const { data } = await deleteHistoryDuplicateGroups('keep_first')
    ElMessage.success(`已删除 ${data.deleted_count} 条重复记录`)
  } catch (error) {
    const message = error instanceof Error ? error.message : ''
    if (!message.includes('引用')) {
      throw error
    }
    await ElMessageBox.confirm('重复记录中存在被引用数据，是否强制删除？', '强制删除确认', {
      type: 'warning',
    })
    const { data } = await deleteHistoryDuplicateGroups('keep_first', true)
    ElMessage.success(`已强制删除 ${data.deleted_count} 条重复记录`)
  }
  await loadAll()
}

async function handlePageChange(nextPage: number) {
  page.value = nextPage
  await loadRecords()
}

async function handlePageSizeChange(nextSize: number) {
  pageSize.value = nextSize
  page.value = 1
  await loadRecords()
}

async function resetFilters() {
  filters.asset_name = ''
  filters.sheet_name = ''
  filters.control_point = ''
  filters.compliance_result = ''
  filters.asset_type = ''
  keyword.value = ''
  page.value = 1
  await loadRecords()
}

async function loadAll() {
  await Promise.all([loadStats(), loadSummary(), loadPhrases(), loadFieldValues(), loadDuplicateGroups(), loadRecords()])
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.panel-value--path {
  font-size: 22px;
  line-height: 1.3;
  word-break: break-all;
}

.panel-meta--list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.phrase-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--workspace-text-secondary);
}

.record-text {
  white-space: pre-wrap;
  line-height: 1.8;
}

.table-footer {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.toolbar-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.duplicate-records {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.duplicate-record-item {
  display: grid;
  grid-template-columns: 120px 1fr 100px;
  gap: 12px;
  color: var(--workspace-text-secondary);
}

.field-value-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--workspace-border-color, #ebeef5);
}

.field-value-main {
  display: flex;
  gap: 12px;
  align-items: center;
}

.field-value-name {
  font-weight: 600;
}

.field-value-count {
  color: var(--workspace-text-secondary);
}

.field-value-actions {
  display: flex;
  gap: 12px;
}

.link-button {
  border: none;
  background: transparent;
  color: var(--el-color-primary);
  cursor: pointer;
  padding: 0;
}

.link-button--danger {
  color: var(--el-color-danger);
}
</style>
