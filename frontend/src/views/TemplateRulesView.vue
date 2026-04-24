<template>
  <AppShell title="模板规则页" subtitle="只读展示字段规则、测评项与模板内容，帮助前端与业务语义对齐。">
    <div class="page-stack">
      <StatsCards :items="summaryCards" />

      <el-row :gutter="16">
        <el-col :xs="24" :xl="8">
          <el-card>
            <template #header>
              <div>
                <div class="section-title">模板目录</div>
                <div class="section-subtitle">展示 templates 数量和模板描述。</div>
              </div>
            </template>
            <div class="stack-list">
              <button
                v-for="template in templateDefinitions"
                :key="template.template_code"
                class="list-card"
                type="button"
                @click="selectedTemplateCode = template.template_code"
              >
                <div class="list-card__title">{{ template.name }}</div>
                <div class="list-card__meta">{{ template.template_code }} · {{ template.domain }}</div>
              </button>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :xl="16">
          <el-card v-if="selectedTemplate">
            <template #header>
              <div>
                <div class="section-title">模板详情</div>
                <div class="section-subtitle">展示 template 内容、字段集合和默认评语。</div>
              </div>
            </template>

            <el-descriptions :column="2" border>
              <el-descriptions-item label="模板名称">{{ selectedTemplate.name }}</el-descriptions-item>
              <el-descriptions-item label="模板编码">{{ selectedTemplate.template_code }}</el-descriptions-item>
              <el-descriptions-item label="领域">{{ selectedTemplate.domain }}</el-descriptions-item>
              <el-descriptions-item label="扩展类型">{{ selectedTemplate.extension_type }}</el-descriptions-item>
              <el-descriptions-item label="描述" :span="2">{{ selectedTemplate.description }}</el-descriptions-item>
              <el-descriptions-item label="字段列表" :span="2">{{ selectedTemplate.field_codes.join('、') }}</el-descriptions-item>
            </el-descriptions>

            <div class="template-blocks">
              <div>
                <div class="template-blocks__label">Title Template</div>
                <pre class="code-block">{{ selectedTemplate.generation.title_template }}</pre>
              </div>
              <div>
                <div class="template-blocks__label">Record Template</div>
                <pre class="code-block">{{ selectedTemplate.generation.record_template }}</pre>
              </div>
              <div>
                <div class="template-blocks__label">Fallbacks</div>
                <pre class="code-block">{{ JSON.stringify(selectedTemplate.generation.fallbacks, null, 2) }}</pre>
              </div>
              <div>
                <div class="template-blocks__label">Default Review Comment</div>
                <pre class="code-block">{{ selectedTemplate.generation.default_review_comment }}</pre>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card>
        <template #header>
          <div>
            <div class="section-title">字段规则</div>
            <div class="section-subtitle">展示 aliases、regex、required_fields 相关抓手。</div>
          </div>
        </template>
        <el-table :data="fieldRules" border>
          <el-table-column prop="field_group" label="字段组" width="120" />
          <el-table-column prop="field_name" label="字段名" width="160" />
          <el-table-column label="Aliases" min-width="220">
            <template #default="scope">
              {{ scope.row.aliases.join('、') }}
            </template>
          </el-table-column>
          <el-table-column label="Regex" min-width="320">
            <template #default="scope">
              <pre class="table-code">{{ scope.row.regex.join('\n') }}</pre>
            </template>
          </el-table-column>
          <el-table-column label="Required" width="100">
            <template #default="scope">
              {{ scope.row.required ? '是' : '否' }}
            </template>
          </el-table-column>
          <el-table-column prop="status_when_missing" label="缺失状态" width="120" />
        </el-table>
      </el-card>

      <el-card>
        <template #header>
          <div>
            <div class="section-title">测评项定义</div>
            <div class="section-subtitle">展示 evaluation_items 数量与 required_fields、设备类型映射。</div>
          </div>
        </template>
        <el-table :data="evaluationItems" border>
          <el-table-column prop="item_code" label="测评项编码" min-width="220" />
          <el-table-column prop="level2" label="二级类目" min-width="140" />
          <el-table-column prop="level3" label="三级类目" min-width="220" />
          <el-table-column label="Required Fields" min-width="220">
            <template #default="scope">
              {{ scope.row.required_fields.join('、') }}
            </template>
          </el-table-column>
          <el-table-column label="Device Types" min-width="160">
            <template #default="scope">
              {{ scope.row.device_types.join('、') }}
            </template>
          </el-table-column>
          <el-table-column prop="pass_score" label="通过阈值" width="120" />
        </el-table>
      </el-card>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import AppShell from '@/components/AppShell.vue'
import StatsCards, { type StatsCardItem } from '@/components/StatsCards.vue'
import { evaluationItems, fieldRules, templateDefinitions } from '@/data/templateRules'

const selectedTemplateCode = ref(templateDefinitions[0]?.template_code || '')
const selectedTemplate = computed(() => templateDefinitions.find((item) => item.template_code === selectedTemplateCode.value) || null)

const summaryCards = computed<StatsCardItem[]>(() => [
  { label: 'templates 数量', value: templateDefinitions.length, tip: '当前内置模板定义', tone: 'primary' },
  { label: 'field_rules 数量', value: fieldRules.length, tip: '字段规则总量', tone: 'success' },
  { label: 'evaluation_items 数量', value: evaluationItems.length, tip: '测评项配置总量', tone: 'warning' },
  { label: '当前模板', value: selectedTemplate.value?.template_code || '-', tip: '选中模板编码', tone: 'default' },
])
</script>

<style scoped>
.stack-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-card {
  padding: 16px;
  border-radius: 16px;
  border: 1px solid #dbe5f1;
  background: #f8fbff;
  text-align: left;
  cursor: pointer;
}

.list-card__title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.list-card__meta {
  margin-top: 6px;
  color: #64748b;
  font-size: 13px;
}

.template-blocks {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 16px;
}

.template-blocks__label {
  margin-bottom: 8px;
  font-size: 12px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.table-code {
  margin: 0;
  white-space: pre-wrap;
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 1280px) {
  .template-blocks {
    grid-template-columns: 1fr;
  }
}
</style>
