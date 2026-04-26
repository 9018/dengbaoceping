import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type {
  EvidenceFactExtractionResult,
  ProjectAssessmentDraftResult,
  ProjectAssessmentItem,
  ProjectAssessmentItemMatchResult,
  ProjectAssessmentTable,
  WorkflowGlobalStatus,
  WorkflowProjectStatus,
} from '@/types/domain'

export interface WorkflowStepState {
  key: string
  title: string
  summary: string
  status: 'not_started' | 'ready' | 'completed' | 'blocked' | 'failed'
  canNext: boolean
}

export const useWorkflowStore = defineStore('workflow', () => {
  const globalStatus = ref<WorkflowGlobalStatus | null>(null)
  const projectStatus = ref<WorkflowProjectStatus | null>(null)
  const projectTables = ref<ProjectAssessmentTable[]>([])
  const projectItems = ref<ProjectAssessmentItem[]>([])
  const extractedFacts = ref<EvidenceFactExtractionResult | null>(null)
  const matchedProjectItem = ref<ProjectAssessmentItemMatchResult | null>(null)
  const generatedDraft = ref<ProjectAssessmentDraftResult | null>(null)
  const currentTableId = ref<string>('')
  const currentEvidenceId = ref<string>('')
  const currentProjectAssessmentItemId = ref<string>('')

  const isReady = computed(() => Boolean(globalStatus.value || projectStatus.value))
  const currentTable = computed(() => projectTables.value.find((item) => item.id === currentTableId.value) || null)
  const currentItem = computed(() => projectItems.value.find((item) => item.id === currentProjectAssessmentItemId.value) || null)

  function setGlobalStatus(value: WorkflowGlobalStatus | null) {
    globalStatus.value = value
  }

  function setProjectStatus(value: WorkflowProjectStatus | null) {
    projectStatus.value = value
  }

  function setProjectTables(value: ProjectAssessmentTable[]) {
    projectTables.value = value
  }

  function setProjectItems(value: ProjectAssessmentItem[]) {
    projectItems.value = value
  }

  function setExtractedFacts(value: EvidenceFactExtractionResult | null) {
    extractedFacts.value = value
  }

  function setMatchedProjectItem(value: ProjectAssessmentItemMatchResult | null) {
    matchedProjectItem.value = value
  }

  function setGeneratedDraft(value: ProjectAssessmentDraftResult | null) {
    generatedDraft.value = value
  }

  function setCurrentTableId(value: string) {
    currentTableId.value = value
  }

  function setCurrentEvidenceId(value: string) {
    currentEvidenceId.value = value
  }

  function setCurrentProjectAssessmentItemId(value: string) {
    currentProjectAssessmentItemId.value = value
  }

  function resetProjectWorkflow() {
    projectStatus.value = null
    projectTables.value = []
    projectItems.value = []
    extractedFacts.value = null
    matchedProjectItem.value = null
    generatedDraft.value = null
    currentTableId.value = ''
    currentEvidenceId.value = ''
    currentProjectAssessmentItemId.value = ''
  }

  return {
    globalStatus,
    projectStatus,
    projectTables,
    projectItems,
    extractedFacts,
    matchedProjectItem,
    generatedDraft,
    currentTableId,
    currentEvidenceId,
    currentProjectAssessmentItemId,
    isReady,
    currentTable,
    currentItem,
    setGlobalStatus,
    setProjectStatus,
    setProjectTables,
    setProjectItems,
    setExtractedFacts,
    setMatchedProjectItem,
    setGeneratedDraft,
    setCurrentTableId,
    setCurrentEvidenceId,
    setCurrentProjectAssessmentItemId,
    resetProjectWorkflow,
  }
})
