<template>
  <ProjectAssessmentWizardView :project-id="projectId" :evidence-id="evidenceId" />
</template>

<script setup lang="ts">
import ProjectAssessmentWizardView from '@/views/ProjectAssessmentWizardView.vue'

defineProps<{ projectId: string; evidenceId?: string }>()
</script>
