<template>
  <AppShell title="指导书管理" subtitle="指导书作为依据库管理，为模板主驱动记录生成提供核查动作、证据要求和判断参考。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">Guidance Library</div>
            <div class="section-title">测评依据知识库管理</div>
            <div class="section-subtitle">当前阶段只做固定路径指导书的导入和查询，不改动记录生成主链路，先把知识库闭环做扎实。</div>
          </div>
          <el-space wrap>
            <el-button @click="loadLibrary">刷新</el-button>
            <el-button type="primary" :loading="importing" @click="handleImport">一键导入</el-button>
          </el-space>
        </div>
      </section>

      <section class="page-grid-3">
        <div class="soft-panel">
          <div class="panel-label">指导书路径</div>
          <div class="panel-value panel-value--path">{{ library.source_file || 'md/指导书.md' }}</div>
          <div class="panel-meta">固定路径，不读取 docs/指导书.md，也不支持其他来源。</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">导入状态</div>
          <div class="panel-value">{{ library.imported ? '已导入' : '未导入' }}</div>
          <div class="panel-meta">当前章节数：{{ library.total || 0 }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">文件状态</div>
          <div class="panel-value">{{ library.file_exists ? (library.file_empty ? '文件为空' : '文件就绪') : '文件缺失' }}</div>
          <div class="panel-meta">{{ library.file_message || '等待检查指导书文件状态。' }}</div>
        </div>
      </section>

      <el-alert
        v-if="library.file_empty"
        title="指导书.md 当前为空，请先补充内容"
        type="warning"
        :closable="false"
        show-icon
      />
      <el-alert
        v-else-if="!library.file_exists"
        :title="library.file_message || '指导书文件不存在，请确认 md/指导书.md 已就位'"
        type="error"
        :closable="false"
        show-icon
      />

      <el-card>
        <template #header>
          <div class="card-toolbar">
            <div class="section-header">
              <div class="section-title">章节列表</div>
              <div class="section-subtitle">支持按章节标题、路径、关键词和正文内容搜索，快速定位测评依据。</div>
            </div>
          </div>
        </template>

        <div class="page-filter-bar">
          <el-form inline @submit.prevent>
            <el-form-item label="关键词">
              <el-input v-model="keyword" clearable placeholder="搜索章节、关键词、核查要点、证据要求" style="width: 360px" @keyup.enter="handleSearch" />
            </el-form-item>
            <el-form-item>
              <el-space>
                <el-button type="primary" @click="handleSearch">搜索</el-button>
                <el-button @click="handleReset">重置</el-button>
              </el-space>
            </el-form-item>
          </el-form>
        </div>

        <el-table :data="library.items" border v-loading="loading">
          <el-table-column prop="section_title" label="章节标题" min-width="180" />
          <el-table-column prop="section_path" label="章节路径" min-width="260" show-overflow-tooltip />
          <el-table-column label="层级" min-width="220">
            <template #default="scope">
              <div class="tag-group">
                <el-tag v-if="scope.row.level1" effect="plain">{{ scope.row.level1 }}</el-tag>
                <el-tag v-if="scope.row.level2" effect="plain" type="success">{{ scope.row.level2 }}</el-tag>
                <el-tag v-if="scope.row.level3" effect="plain" type="warning">{{ scope.row.level3 }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="关键词" min-width="220">
            <template #default="scope">
              <div class="tag-group">
                <el-tag v-for="item in scope.row.keywords_json.slice(0, 6)" :key="item" size="small" effect="plain">{{ item }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="核查要点" min-width="240" show-overflow-tooltip>
            <template #default="scope">
              {{ scope.row.check_points_json[0] || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="scope">
              <el-button size="small" type="primary" @click="openDetail(scope.row.id)">查看详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-drawer v-model="detailVisible" title="指导书章节详情" size="720px">
        <div v-if="detailItem" class="page-stack">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="章节标题">{{ detailItem.section_title }}</el-descriptions-item>
            <el-descriptions-item label="章节编码">{{ detailItem.guidance_code }}</el-descriptions-item>
            <el-descriptions-item label="来源文件">{{ detailItem.source_file }}</el-descriptions-item>
            <el-descriptions-item label="章节路径">{{ detailItem.section_path }}</el-descriptions-item>
          </el-descriptions>

          <div class="page-grid-2">
            <el-card>
              <template #header>
                <div class="section-header">
                  <div class="section-title">关键词</div>
                  <div class="section-subtitle">规则版关键词抽取结果</div>
                </div>
              </template>
              <div class="tag-group">
                <el-tag v-for="item in detailItem.keywords_json" :key="item" effect="plain">{{ item }}</el-tag>
              </div>
            </el-card>

            <el-card>
              <template #header>
                <div class="section-header">
                  <div class="section-title">记录建议</div>
                  <div class="section-subtitle">为后续记录生成预留的建议内容</div>
                </div>
              </template>
              <div class="muted-text">{{ detailItem.record_suggestion || '当前章节暂无记录建议。' }}</div>
            </el-card>
          </div>

          <el-card>
            <template #header>
              <div class="section-header">
                <div class="section-title">相似历史记录</div>
                <div class="section-subtitle">把当前章节与历史人工写法样本做规则关联，沉淀可复用参考。</div>
              </div>
            </template>
            <div class="page-filter-bar guidance-history-toolbar">
              <el-form inline @submit.prevent>
                <el-form-item label="符合情况">
                  <el-select v-model="detailHistoryFilter" clearable placeholder="全部状态" style="width: 180px" @change="handleDetailHistoryFilterChange">
                    <el-option v-for="item in detailHistoryStatusOptions" :key="item" :label="item" :value="item" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-space>
                    <el-button :loading="historyLoading" @click="reloadDetailHistory">刷新列表</el-button>
                    <el-button type="primary" :loading="linkingHistory" @click="refreshGuidanceHistoryLinks">刷新关联</el-button>
                  </el-space>
                </el-form-item>
              </el-form>
            </div>
            <el-table :data="detailHistoryRows" border v-loading="historyLoading">
              <el-table-column prop="match_score" label="得分" width="88" />
              <el-table-column prop="compliance_status" label="符合情况" width="110" />
              <el-table-column prop="sheet_name" label="Sheet" min-width="140" />
              <el-table-column prop="asset_type" label="资产类型" width="120" />
              <el-table-column prop="control_point" label="控制点" min-width="180" show-overflow-tooltip />
              <el-table-column prop="evaluation_item" label="测评项" min-width="180" show-overflow-tooltip />
              <el-table-column label="命中原因" min-width="220" show-overflow-tooltip>
                <template #default="scope">
                  {{ scope.row.match_reason.summary.join('；') || '-' }}
                </template>
              </el-table-column>
              <el-table-column label="结果记录摘要" min-width="260" show-overflow-tooltip>
                <template #default="scope">
                  {{ scope.row.record_text || '-' }}
                </template>
              </el-table-column>
            </el-table>
            <div v-if="!historyLoading && !detailHistoryRows.length" class="empty-tip">
              当前章节还没有关联历史记录，可点击“刷新关联”重算样本。
            </div>
          </el-card>

          <el-card>
            <template #header>
              <div class="section-header">
                <div class="section-title">核查要点</div>
                <div class="section-subtitle">从章节正文中提取的检查动作</div>
              </div>
            </template>
            <ul class="detail-list">
              <li v-for="item in detailItem.check_points_json" :key="item">{{ item }}</li>
              <li v-if="!detailItem.check_points_json.length">暂无核查要点。</li>
            </ul>
          </el-card>

          <el-card>
            <template #header>
              <div class="section-header">
                <div class="section-title">证据要求</div>
                <div class="section-subtitle">从章节正文中提取的证据线索</div>
              </div>
            </template>
            <ul class="detail-list">
              <li v-for="item in detailItem.evidence_requirements_json" :key="item">{{ item }}</li>
              <li v-if="!detailItem.evidence_requirements_json.length">暂无证据要求。</li>
            </ul>
          </el-card>

          <el-card>
            <template #header>
              <div class="section-header">
                <div class="section-title">正文内容</div>
                <div class="section-subtitle">保留章节原始 Markdown 和纯文本，便于后续规则接入。</div>
              </div>
            </template>
            <div class="page-grid-2">
              <div>
                <div class="template-blocks__label">Raw Markdown</div>
                <pre class="code-block code-block--tall">{{ detailItem.raw_markdown }}</pre>
              </div>
              <div>
                <div class="template-blocks__label">Plain Text</div>
                <pre class="code-block code-block--tall">{{ detailItem.plain_text }}</pre>
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
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import {
  getGuidanceItem,
  importGuidanceMarkdown,
  linkGuidanceHistory,
  listGuidanceHistoryRecords,
  listGuidanceItems,
} from '@/api/guidance'
import type { GuidanceHistoryMatch, GuidanceItem, GuidanceLibrary } from '@/types/domain'

const loading = ref(false)
const importing = ref(false)
const detailVisible = ref(false)
const detailItem = ref<GuidanceItem | null>(null)
const historyLoading = ref(false)
const linkingHistory = ref(false)
const detailHistoryRows = ref<GuidanceHistoryMatch[]>([])
const detailHistoryFilter = ref('')
const keyword = ref('')
const library = reactive<GuidanceLibrary>({
  source_file: 'md/指导书.md',
  absolute_path: '',
  file_exists: false,
  file_empty: false,
  file_message: '',
  imported: false,
  total: 0,
  keyword: null,
  items: [],
})

const detailHistoryStatusOptions = computed(() => {
  return Array.from(new Set(detailHistoryRows.value.map((item) => item.compliance_status).filter(Boolean))) as string[]
})

function syncLibrary(data: GuidanceLibrary) {
  library.source_file = data.source_file
  library.absolute_path = data.absolute_path
  library.file_exists = data.file_exists
  library.file_empty = data.file_empty
  library.file_message = data.file_message
  library.imported = data.imported
  library.total = data.total
  library.keyword = data.keyword
  library.items = data.items
}

async function loadLibrary(searchKeyword?: string) {
  loading.value = true
  try {
    const normalizedKeyword = searchKeyword?.trim() || undefined
    const { data } = await listGuidanceItems(normalizedKeyword)
    syncLibrary(data)
  } finally {
    loading.value = false
  }
}

async function handleImport() {
  importing.value = true
  try {
    const { message } = await importGuidanceMarkdown()
    ElMessage.success(message || '指导书导入成功')
    await loadLibrary(keyword.value)
  } finally {
    importing.value = false
  }
}

async function loadDetailHistory(guidanceId: string, complianceStatus?: string) {
  historyLoading.value = true
  try {
    const { data } = await listGuidanceHistoryRecords(guidanceId, complianceStatus)
    detailHistoryRows.value = data
  } finally {
    historyLoading.value = false
  }
}

async function openDetail(guidanceId: string) {
  detailHistoryFilter.value = ''
  detailHistoryRows.value = []
  const [{ data: detailData }] = await Promise.all([
    getGuidanceItem(guidanceId),
  ])
  detailItem.value = detailData
  detailVisible.value = true
  await loadDetailHistory(guidanceId)
}

async function reloadDetailHistory() {
  if (!detailItem.value) return
  await loadDetailHistory(detailItem.value.id, detailHistoryFilter.value || undefined)
}

async function handleDetailHistoryFilterChange() {
  await reloadDetailHistory()
}

async function refreshGuidanceHistoryLinks() {
  if (!detailItem.value) return
  linkingHistory.value = true
  try {
    const { data, message } = await linkGuidanceHistory(detailItem.value.id)
    ElMessage.success(message || `已刷新 ${data.linked_count} 条关联结果`)
    await reloadDetailHistory()
  } finally {
    linkingHistory.value = false
  }
}

async function handleSearch() {
  await loadLibrary(keyword.value)
}

async function handleReset() {
  keyword.value = ''
  await loadLibrary()
}

onMounted(() => {
  loadLibrary()
})
</script>

<style scoped>
.panel-value--path {
  font-size: 22px;
  line-height: 1.3;
  word-break: break-all;
}

.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
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

.guidance-history-toolbar {
  margin-bottom: 12px;
}

.empty-tip {
  padding-top: 12px;
  color: var(--workspace-text-secondary);
}
</style>
