<template>
  <AppShell title="初始化向导" subtitle="先把全局模板库、指导书依据库和历史写法样本库准备好，再进入项目内测评主流程。">
    <div class="page-stack">
      <section class="page-section">
        <div class="page-header">
          <div class="page-header__content">
            <div class="section-kicker">Setup Wizard</div>
            <div class="section-title">全局知识库初始化</div>
            <div class="section-subtitle">导入结果记录参考模板、指导书和历史人工测评记录，为项目内测评表生成与草稿写回提供统一底座。</div>
          </div>
          <el-space wrap>
            <el-button @click="loadStatus">刷新状态</el-button>
          </el-space>
        </div>
      </section>

      <section class="page-grid-3">
        <div class="soft-panel">
          <div class="panel-label">模板工作簿</div>
          <div class="panel-value">{{ workflowStore.globalStatus?.template_workbook_count || 0 }}</div>
          <div class="panel-meta">模板项：{{ workflowStore.globalStatus?.template_item_count || 0 }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">指导书条目</div>
          <div class="panel-value">{{ workflowStore.globalStatus?.guidance_item_count || 0 }}</div>
          <div class="panel-meta">状态：{{ workflowStore.globalStatus?.status || 'not_started' }}</div>
        </div>
        <div class="soft-panel">
          <div class="panel-label">历史记录样本</div>
          <div class="panel-value">{{ workflowStore.globalStatus?.history_record_count || 0 }}</div>
          <div class="panel-meta">{{ workflowStore.globalStatus?.summary || '等待初始化' }}</div>
        </div>
      </section>

      <el-card>
        <template #header>
          <div class="section-header">
            <div class="section-title">初始化步骤</div>
            <div class="section-subtitle">每一步都可重复刷新，确保导入结果和后端状态保持一致。</div>
          </div>
        </template>
        <div class="wizard-stack">
          <WorkflowStepper :active="activeStep" :steps="steps" />

          <TemplateImportStep
            v-if="activeStep === 0"
            :summary="workflowStore.globalStatus"
            @import="handleTemplateImport"
            @refresh="loadStatus"
          />
          <GuidanceImportStep
            v-else-if="activeStep === 1"
            :summary="workflowStore.globalStatus"
            @import="handleGuidanceImport"
            @refresh="loadStatus"
          />
          <HistoryImportStep
            v-else
            :summary="workflowStore.globalStatus"
            @import="handleHistoryImport"
            @refresh="loadStatus"
          />

          <StepFooterActions
            v-if="activeStep < steps.length - 1"
            :show-previous="activeStep > 0"
            :disabled="nextDisabled"
            @previous="activeStep -= 1"
            @next="activeStep += 1"
          />
          <div v-else class="step-end-actions">
            <el-button @click="activeStep -= 1">上一步</el-button>
          </div>
        </div>
      </el-card>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import GuidanceImportStep from '@/components/assessment/GuidanceImportStep.vue'
import HistoryImportStep from '@/components/assessment/HistoryImportStep.vue'
import TemplateImportStep from '@/components/assessment/TemplateImportStep.vue'
import StepFooterActions from '@/components/workflow/StepFooterActions.vue'
import WorkflowStepper from '@/components/workflow/WorkflowStepper.vue'
import { getWorkflowGlobalStatus, importWorkflowGuidance, importWorkflowHistory, importWorkflowTemplate } from '@/api/workflow'
import { useWorkflowStore } from '@/stores/workflow'

const workflowStore = useWorkflowStore()
const activeStep = ref(0)

const steps = [
  { key: 'template', title: '导入模板', summary: '生成全局测评项模板库' },
  { key: 'guidance', title: '导入指导书', summary: '补充依据、检查点和证据要求' },
  { key: 'history', title: '导入历史记录', summary: '沉淀人工写法样本和符合情况样本' },
]

const nextDisabled = computed(() => {
  if (activeStep.value === 0) return !workflowStore.globalStatus?.template_workbook_count
  if (activeStep.value === 1) return !workflowStore.globalStatus?.guidance_item_count
  return false
})

async function loadStatus() {
  const { data } = await getWorkflowGlobalStatus()
  workflowStore.setGlobalStatus(data)
}

async function handleTemplateImport(file: File) {
  const { message } = await importWorkflowTemplate(file)
  ElMessage.success(message || '模板导入成功')
  await loadStatus()
}

async function handleGuidanceImport() {
  const { message } = await importWorkflowGuidance()
  ElMessage.success(message || '指导书导入成功')
  await loadStatus()
}

async function handleHistoryImport(file: File) {
  const { message } = await importWorkflowHistory(file)
  ElMessage.success(message || '历史记录导入成功')
  await loadStatus()
}

onMounted(loadStatus)
</script>

<style scoped>
.wizard-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.step-end-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
