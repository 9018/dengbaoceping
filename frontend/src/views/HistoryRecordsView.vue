<template>
  <AppShell title="历史记录库" subtitle="导入人工三级测评 Excel，沉淀结构化样本库，支持筛选、搜索、相似记录和句式统计。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">History Library</div>
            <div class="section-title">历史人工测评记录库</div>
            <div class="section-subtitle">当前阶段只做 Excel 入库、结构化查询、规则搜索与参考统计，不改动现有记录生成主链路。</div>
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
            <div class="section-title">历史记录检索</div>
            <div class="section-subtitle">按 sheet、控制点、符合情况、资产类型过滤，并支持关键词搜索历史人工样本。</div>
          </div>
        </template>

        <div class="page-filter-bar">
          <el-form inline @submit.prevent>
            <el-form-item label="Sheet">
              <el-select v-model="filters.sheet_name" clearable filterable placeholder="全部工作表" style="width: 220px">
                <el-option v-for="item in sheetOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="控制点">
              <el-input v-model="filters.control_point" clearable placeholder="输入控制点关键词" style="width: 220px" />
            </el-form-item>
            <el-form-item label="符合情况">
              <el-select v-model="filters.compliance_status" clearable placeholder="全部状态" style="width: 180px">
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
          <el-table-column prop="sheet_name" label="Sheet" min-width="160" />
          <el-table-column prop="asset_type" label="资产类型" width="120" />
          <el-table-column prop="control_point" label="控制点" min-width="180" show-overflow-tooltip />
          <el-table-column prop="evaluation_item" label="测评项" min-width="220" show-overflow-tooltip />
          <el-table-column prop="compliance_status" label="符合情况" width="120" />
          <el-table-column prop="score" label="分值" width="90" />
          <el-table-column prop="item_no" label="编号" width="110" />
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
      </el-card>

      <div class="page-grid-2">
        <el-card>
          <template #header>
            <div class="section-header">
              <div class="section-title">相似样本</div>
              <div class="section-subtitle">基于控制点、测评项和资产类型的规则打分，返回最接近的历史记录。</div>
            </div>
          </template>
          <el-form label-width="88px" @submit.prevent>
            <el-form-item label="控制点">
              <el-input v-model="similarQuery.control_point" clearable placeholder="例如：边界访问控制" />
            </el-form-item>
            <el-form-item label="测评项">
              <el-input v-model="similarQuery.evaluation_item" clearable placeholder="例如：应限制非授权访问" />
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
            <el-table-column prop="compliance_status" label="符合情况" width="120" />
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
                  <div v-for="(total, key) in scope.row.compliance_status_counts" :key="key">{{ key }}：{{ total }}</div>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <el-drawer v-model="detailVisible" title="历史记录详情" size="720px">
        <div v-if="detailItem" class="page-stack">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="来源文件">{{ detailItem.source_file }}</el-descriptions-item>
            <el-descriptions-item label="Sheet">{{ detailItem.sheet_name }}</el-descriptions-item>
            <el-descriptions-item label="资产名称">{{ detailItem.asset_name }}</el-descriptions-item>
            <el-descriptions-item label="资产类型">{{ detailItem.asset_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="控制点">{{ detailItem.control_point || '-' }}</el-descriptions-item>
            <el-descriptions-item label="测评项">{{ detailItem.evaluation_item || '-' }}</el-descriptions-item>
            <el-descriptions-item label="符合情况">{{ detailItem.compliance_status || '-' }}</el-descriptions-item>
            <el-descriptions-item label="编号 / 分值">{{ detailItem.item_no || '-' }} / {{ detailItem.score ?? '-' }}</el-descriptions-item>
          </el-descriptions>

          <el-card>
            <template #header>
              <div class="section-header">
                <div class="section-title">结果记录</div>
                <div class="section-subtitle">保留人工原始写法，便于横向参考。</div>
              </div>
            </template>
            <div class="muted-text record-text">{{ detailItem.record_text || '暂无结果记录。' }}</div>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, type UploadFile } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import StatsCards, { type StatsCardItem } from '@/components/StatsCards.vue'
import {
  getHistoryPhrases,
  getHistoryRecord,
  getHistorySimilarRecords,
  getHistoryStats,
  importHistoryExcel,
  listHistoryRecords,
  searchHistoryRecords,
} from '@/api/history'
import type {
  HistoryImportResult,
  HistoryPhraseSummary,
  HistoryRecord,
  HistorySimilarRecord,
  HistoryStats,
} from '@/types/domain'

const loading = ref(false)
const importing = ref(false)
const detailVisible = ref(false)
const detailItem = ref<HistoryRecord | null>(null)
const rows = ref<HistoryRecord[]>([])
const phrases = ref<HistoryPhraseSummary[]>([])
const similarRows = ref<HistorySimilarRecord[]>([])
const keyword = ref('')
const lastImport = ref<HistoryImportResult | null>(null)
const stats = ref<HistoryStats>({
  sheet_count: 0,
  total: 0,
  compliance_status_counts: {},
  asset_type_counts: {},
})
const filters = reactive({
  sheet_name: '',
  control_point: '',
  compliance_status: '',
  asset_type: '',
})
const similarQuery = reactive({
  control_point: '',
  evaluation_item: '',
  asset_type: '',
})

const summaryCards = computed<StatsCardItem[]>(() => [
  { label: '工作表数量', value: stats.value.sheet_count, tip: '已导入的 Sheet 数', tone: 'primary' },
  { label: '记录总数', value: stats.value.total, tip: '全部历史人工记录', tone: 'success' },
  { label: '资产类型', value: Object.keys(stats.value.asset_type_counts).length, tip: '已识别资产类型数', tone: 'default' },
  { label: '符合状态', value: Object.keys(stats.value.compliance_status_counts).length, tip: '已沉淀符合情况种类', tone: 'warning' },
])

const sheetOptions = computed(() => Array.from(new Set(rows.value.map((item) => item.sheet_name))).filter(Boolean))
const complianceOptions = computed(() => Object.keys(stats.value.compliance_status_counts))
const assetTypeOptions = computed(() => Object.keys(stats.value.asset_type_counts))

async function loadStats() {
  const { data } = await getHistoryStats()
  stats.value = data
}

async function loadPhrases() {
  const { data } = await getHistoryPhrases()
  phrases.value = data
}

async function loadRecords() {
  loading.value = true
  try {
    const normalizedKeyword = keyword.value.trim()
    if (normalizedKeyword) {
      const { data } = await searchHistoryRecords(normalizedKeyword)
      rows.value = data.filter((item) => {
        return (!filters.sheet_name || item.sheet_name === filters.sheet_name)
          && (!filters.control_point || (item.control_point || '').includes(filters.control_point.trim()))
          && (!filters.compliance_status || item.compliance_status === filters.compliance_status)
          && (!filters.asset_type || item.asset_type === filters.asset_type)
      })
      return
    }
    const { data } = await listHistoryRecords({
      sheet_name: filters.sheet_name || undefined,
      control_point: filters.control_point || undefined,
      compliance_status: filters.compliance_status || undefined,
      asset_type: filters.asset_type || undefined,
    })
    rows.value = data
  } finally {
    loading.value = false
  }
}

async function loadSimilar() {
  if (!similarQuery.control_point.trim() || !similarQuery.evaluation_item.trim()) {
    ElMessage.warning('请先填写控制点和测评项')
    return
  }
  const { data } = await getHistorySimilarRecords({
    control_point: similarQuery.control_point.trim(),
    evaluation_item: similarQuery.evaluation_item.trim(),
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

async function resetFilters() {
  filters.sheet_name = ''
  filters.control_point = ''
  filters.compliance_status = ''
  filters.asset_type = ''
  keyword.value = ''
  await loadRecords()
}

async function loadAll() {
  await Promise.all([loadStats(), loadPhrases(), loadRecords()])
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
</style>
