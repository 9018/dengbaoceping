<template>
  <AppShell title="测评记录模板库" subtitle="把结果记录参考模板 Excel 结构化沉淀为全局主模板库，支持导入、统计、筛选和逐项查看。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">Assessment Template Library</div>
            <div class="section-title">结果记录主模板库</div>
            <div class="section-subtitle">以全局模板库方式管理结果记录参考模板，供后续模板驱动记录生成持续复用。</div>
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

      <section v-if="lastImport" class="page-grid-3">
        <div class="soft-panel">
          <div class="panel-label">最近导入文件</div>
          <div class="panel-value panel-value--path">{{ lastImport.source_file }}</div>
          <div class="panel-meta">版本：{{ lastImport.version || '未识别' }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">导入结果</div>
          <div class="panel-value">{{ lastImport.imported_count }}</div>
          <div class="panel-meta">工作表 {{ lastImport.sheet_count }} / 跳过 {{ lastImport.skipped_count }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">当前工作簿</div>
          <div class="panel-value">{{ activeWorkbook?.name || '未选择' }}</div>
          <div class="panel-meta">模板项 {{ activeWorkbook?.item_count || 0 }}</div>
        </div>
      </section>

      <el-card>
        <template #header>
          <div class="section-header">
            <div class="section-title">模板工作簿</div>
            <div class="section-subtitle">查看已导入版本，并切换当前分析对象。</div>
          </div>
        </template>
        <el-table :data="workbooks" border v-loading="loadingWorkbooks" highlight-current-row @current-change="handleWorkbookSelect">
          <el-table-column prop="name" label="模板名称" min-width="220" />
          <el-table-column prop="version" label="版本" width="120" />
          <el-table-column prop="source_file" label="来源文件" min-width="240" show-overflow-tooltip />
          <el-table-column prop="sheet_count" label="Sheet 数" width="100" />
          <el-table-column prop="item_count" label="模板项数" width="110" />
        </el-table>
      </el-card>

      <section class="page-grid-3" v-if="activeWorkbookDetail">
        <div class="soft-panel">
          <div class="panel-label">对象类型分布</div>
          <div class="panel-meta panel-meta--list">
            <div v-for="(total, key) in activeWorkbookDetail.object_type_counts" :key="key">{{ key }}：{{ total }}</div>
          </div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">对象分类分布</div>
          <div class="panel-meta panel-meta--list">
            <div v-for="(total, key) in activeWorkbookDetail.object_category_counts" :key="key">{{ key }}：{{ total }}</div>
          </div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">控制点 Top</div>
          <div class="panel-meta panel-meta--list">
            <div v-for="item in topControlPoints" :key="item.label">{{ item.label }}：{{ item.total }}</div>
          </div>
        </div>
      </section>

      <div class="page-grid-2">
        <el-card>
          <template #header>
            <div class="section-header">
              <div class="section-title">Sheet 列表</div>
              <div class="section-subtitle">查看对象类型推断结果和行数分布。</div>
            </div>
          </template>
          <el-table :data="sheets" border v-loading="loadingSheets">
            <el-table-column prop="sheet_name" label="Sheet" min-width="180" />
            <el-table-column prop="object_type" label="对象类型" width="120" />
            <el-table-column prop="object_category" label="对象分类" width="120" />
            <el-table-column prop="object_subtype" label="对象子类" width="120" />
            <el-table-column prop="row_count" label="模板项数" width="100" />
          </el-table>
        </el-card>

        <el-card>
          <template #header>
            <div class="section-header">
              <div class="section-title">筛选条件</div>
              <div class="section-subtitle">按 Sheet、对象类型、控制点、编号、页面类型和关键词过滤模板项。</div>
            </div>
          </template>
          <el-form label-width="88px" @submit.prevent>
            <el-form-item label="Sheet">
              <el-select v-model="filters.sheet_name" clearable filterable placeholder="全部 Sheet">
                <el-option v-for="item in sheetOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="对象类型">
              <el-select v-model="filters.object_type" clearable placeholder="全部类型">
                <el-option v-for="item in objectTypeOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="对象分类">
              <el-select v-model="filters.object_category" clearable placeholder="全部分类">
                <el-option v-for="item in objectCategoryOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="控制点">
              <el-input v-model="filters.control_point" clearable placeholder="输入控制点关键词" />
            </el-form-item>
            <el-form-item label="编号">
              <el-input v-model="filters.item_code" clearable placeholder="输入模板编号" />
            </el-form-item>
            <el-form-item label="页面类型">
              <el-select v-model="filters.page_type" clearable placeholder="全部类型">
                <el-option v-for="item in pageTypeOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="关键词">
              <el-input v-model="filters.keyword" clearable placeholder="搜索测评项/结果记录/关键词" @keyup.enter="loadItems" />
            </el-form-item>
            <el-form-item>
              <el-space>
                <el-button type="primary" @click="loadItems">查询</el-button>
                <el-button @click="resetFilters">重置</el-button>
              </el-space>
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <el-card>
        <template #header>
          <div class="section-header">
            <div class="section-title">模板项列表</div>
            <div class="section-subtitle">直接查看 A-G 字段、对象推断结果与扩展模板线索。</div>
          </div>
        </template>
        <el-table :data="items" border v-loading="loadingItems">
          <el-table-column prop="sheet_name" label="Sheet" min-width="160" />
          <el-table-column prop="item_code" label="编号" width="110" />
          <el-table-column prop="standard_type" label="扩展标准" min-width="150" show-overflow-tooltip />
          <el-table-column prop="control_point" label="控制点" min-width="180" show-overflow-tooltip />
          <el-table-column prop="item_text" label="测评项" min-width="220" show-overflow-tooltip />
          <el-table-column prop="default_compliance_result" label="符合情况" width="120" />
          <el-table-column prop="weight" label="权重" width="90" />
          <el-table-column label="页面类型" min-width="180">
            <template #default="scope">
              <div class="tag-group">
                <el-tag v-for="item in normalizeStringArray(scope.row.page_types_json)" :key="item" size="small" effect="plain">{{ item }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="证据关键词" min-width="220">
            <template #default="scope">
              <div class="tag-group">
                <el-tag v-for="item in normalizeStringArray(scope.row.evidence_keywords_json).slice(0, 6)" :key="item" size="small" effect="plain">{{ item }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="scope">
              <el-button size="small" type="primary" @click="openDetail(scope.row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-drawer v-model="detailVisible" title="模板项详情" size="760px">
        <div v-if="detailItem" class="page-stack">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="Sheet">{{ detailItem.sheet_name }}</el-descriptions-item>
            <el-descriptions-item label="行号">{{ detailItem.row_index }}</el-descriptions-item>
            <el-descriptions-item label="编号">{{ detailItem.item_code || '-' }}</el-descriptions-item>
            <el-descriptions-item label="对象类型 / 分类">{{ detailItem.object_type || '-' }} / {{ detailItem.object_category || '-' }}</el-descriptions-item>
            <el-descriptions-item label="扩展标准">{{ detailItem.standard_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="控制点">{{ detailItem.control_point || '-' }}</el-descriptions-item>
            <el-descriptions-item label="测评项">{{ detailItem.item_text || '-' }}</el-descriptions-item>
            <el-descriptions-item label="符合情况 / 权重">{{ detailItem.default_compliance_result || '-' }} / {{ detailItem.weight ?? '-' }}</el-descriptions-item>
          </el-descriptions>

          <el-card>
            <template #header>
              <div class="section-header">
                <div class="section-title">结果记录模板</div>
                <div class="section-subtitle">D 列主模板正文。</div>
              </div>
            </template>
            <div class="muted-text record-text">{{ detailItem.record_template || '暂无结果记录模板。' }}</div>
          </el-card>

          <div class="page-grid-2">
            <el-card>
              <template #header>
                <div class="section-header">
                  <div class="section-title">页面类型 / 适用范围</div>
                  <div class="section-subtitle">规则推断的后续使用线索。</div>
                </div>
              </template>
              <div class="tag-group">
                <el-tag v-for="item in normalizeStringArray(detailItem.page_types_json)" :key="item" effect="plain">{{ item }}</el-tag>
                <el-tag v-for="item in normalizeStringArray(detailItem.applicability_json)" :key="`app-${item}`" type="success" effect="plain">{{ item }}</el-tag>
              </div>
            </el-card>

            <el-card>
              <template #header>
                <div class="section-header">
                  <div class="section-title">必备事实 / 命令关键词</div>
                  <div class="section-subtitle">供后续证据匹配和页面分类复用。</div>
                </div>
              </template>
              <div class="tag-group">
                <el-tag v-for="item in normalizeStringArray(detailItem.required_facts_json)" :key="item" type="warning" effect="plain">{{ item }}</el-tag>
                <el-tag v-for="item in normalizeStringArray(detailItem.command_keywords_json)" :key="`cmd-${item}`" type="info" effect="plain">{{ item }}</el-tag>
              </div>
            </el-card>
          </div>

          <el-card>
            <template #header>
              <div class="section-header">
                <div class="section-title">原始行数据 / 扩展模板</div>
                <div class="section-subtitle">保留 H/I/J 等额外写法样例，方便横向参考。</div>
              </div>
            </template>
            <div class="page-grid-2">
              <div>
                <div class="panel-label">扩展模板</div>
                <ul class="detail-list">
                  <li v-for="item in alternativeTemplates" :key="item">{{ item }}</li>
                  <li v-if="!alternativeTemplates.length">暂无扩展模板。</li>
                </ul>
              </div>
              <div>
                <div class="panel-label">原始行 JSON</div>
                <pre class="code-block code-block--tall">{{ formattedRawRow }}</pre>
              </div>
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
  getAssessmentTemplateWorkbook,
  importAssessmentTemplateExcel,
  listAssessmentTemplateItems,
  listAssessmentTemplateSheets,
  listAssessmentTemplateWorkbooks,
} from '@/api/assessmentTemplates'
import type {
  AssessmentTemplateImportResult,
  AssessmentTemplateItem,
  AssessmentTemplateSheet,
  AssessmentTemplateWorkbook,
  AssessmentTemplateWorkbookDetail,
} from '@/types/domain'

const importing = ref(false)
const loadingWorkbooks = ref(false)
const loadingSheets = ref(false)
const loadingItems = ref(false)
const detailVisible = ref(false)
const lastImport = ref<AssessmentTemplateImportResult | null>(null)
const workbooks = ref<AssessmentTemplateWorkbook[]>([])
const activeWorkbook = ref<AssessmentTemplateWorkbook | null>(null)
const activeWorkbookDetail = ref<AssessmentTemplateWorkbookDetail | null>(null)
const sheets = ref<AssessmentTemplateSheet[]>([])
const items = ref<AssessmentTemplateItem[]>([])
const detailItem = ref<AssessmentTemplateItem | null>(null)
const filters = reactive({
  sheet_name: '',
  object_type: '',
  object_category: '',
  control_point: '',
  item_code: '',
  keyword: '',
  page_type: '',
})

const summaryCards = computed<StatsCardItem[]>(() => [
  { label: '工作簿版本', value: workbooks.value.length, tip: '已导入模板版本数', tone: 'primary' },
  { label: 'Sheet 数', value: activeWorkbookDetail.value?.sheet_count || 0, tip: '当前工作簿工作表数量', tone: 'success' },
  { label: '模板项数', value: activeWorkbookDetail.value?.item_count || 0, tip: '当前工作簿模板项总量', tone: 'warning' },
  { label: '对象类型', value: Object.keys(activeWorkbookDetail.value?.object_type_counts || {}).length, tip: '当前工作簿对象类型种类', tone: 'default' },
])

const sheetOptions = computed(() => sheets.value.map((item) => item.sheet_name))
const objectTypeOptions = computed(() => Object.keys(activeWorkbookDetail.value?.object_type_counts || {}))
const objectCategoryOptions = computed(() => Object.keys(activeWorkbookDetail.value?.object_category_counts || {}))
const pageTypeOptions = computed(() => Array.from(new Set(items.value.flatMap((item) => normalizeStringArray(item.page_types_json)))))
const topControlPoints = computed(() => {
  return Object.entries(activeWorkbookDetail.value?.control_point_counts || {})
    .map(([label, total]) => ({ label, total }))
    .sort((left, right) => right.total - left.total)
    .slice(0, 6)
})
const alternativeTemplates = computed(() => {
  if (!detailItem.value?.raw_row_json || Array.isArray(detailItem.value.raw_row_json)) return []
  const value = detailItem.value.raw_row_json.alternative_templates
  return Array.isArray(value) ? value.map((item) => String(item)) : []
})
const formattedRawRow = computed(() => JSON.stringify(detailItem.value?.raw_row_json || {}, null, 2))

function normalizeStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)) : []
}

async function loadWorkbooks() {
  loadingWorkbooks.value = true
  try {
    const { data } = await listAssessmentTemplateWorkbooks()
    workbooks.value = data
    if (!activeWorkbook.value && data.length) {
      activeWorkbook.value = data[0]
    } else if (activeWorkbook.value) {
      activeWorkbook.value = data.find((item) => item.id === activeWorkbook.value?.id) || data[0] || null
    }
  } finally {
    loadingWorkbooks.value = false
  }
}

async function loadWorkbookDetail() {
  if (!activeWorkbook.value) {
    activeWorkbookDetail.value = null
    sheets.value = []
    items.value = []
    return
  }
  loadingSheets.value = true
  try {
    const [{ data: detail }, { data: sheetRows }] = await Promise.all([
      getAssessmentTemplateWorkbook(activeWorkbook.value.id),
      listAssessmentTemplateSheets(activeWorkbook.value.id),
    ])
    activeWorkbookDetail.value = detail
    sheets.value = sheetRows
  } finally {
    loadingSheets.value = false
  }
}

async function loadItems() {
  if (!activeWorkbook.value) {
    items.value = []
    return
  }
  loadingItems.value = true
  try {
    const { data } = await listAssessmentTemplateItems({
      workbook_id: activeWorkbook.value.id,
      sheet_name: filters.sheet_name || undefined,
      object_type: filters.object_type || undefined,
      object_category: filters.object_category || undefined,
      control_point: filters.control_point || undefined,
      item_code: filters.item_code || undefined,
      keyword: filters.keyword.trim() || undefined,
      page_type: filters.page_type || undefined,
    })
    items.value = data
  } finally {
    loadingItems.value = false
  }
}

async function loadAll() {
  await loadWorkbooks()
  await loadWorkbookDetail()
  await loadItems()
}

async function handleFileChange(uploadFile: UploadFile) {
  const raw = uploadFile.raw
  if (!raw) return
  importing.value = true
  try {
    const { data, message } = await importAssessmentTemplateExcel(raw)
    lastImport.value = data
    ElMessage.success(message || '测评记录模板导入成功')
    activeWorkbook.value = null
    await loadAll()
  } finally {
    importing.value = false
  }
}

async function handleWorkbookSelect(workbook: AssessmentTemplateWorkbook | undefined) {
  activeWorkbook.value = workbook || null
  await loadWorkbookDetail()
  await loadItems()
}

async function resetFilters() {
  filters.sheet_name = ''
  filters.object_type = ''
  filters.object_category = ''
  filters.control_point = ''
  filters.item_code = ''
  filters.keyword = ''
  filters.page_type = ''
  await loadItems()
}

function openDetail(item: AssessmentTemplateItem) {
  detailItem.value = item
  detailVisible.value = true
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

.record-text {
  white-space: pre-wrap;
  line-height: 1.8;
}

.detail-list {
  margin: 0;
  padding-left: 18px;
  color: var(--workspace-text-secondary);
  line-height: 1.8;
}

.code-block--tall {
  min-height: 240px;
  white-space: pre-wrap;
}
</style>
