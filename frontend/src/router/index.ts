import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
    },
    {
      path: '/setup-wizard',
      name: 'setup-wizard',
      component: () => import('@/views/GlobalSetupWizardView.vue'),
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('@/views/ProjectsView.vue'),
    },
    {
      path: '/projects/:projectId',
      name: 'project-detail',
      component: () => import('@/views/ProjectDetailView.vue'),
      props: true,
    },
    {
      path: '/projects/:projectId/assessment-wizard',
      name: 'assessment-wizard',
      component: () => import('@/views/ProjectAssessmentWizardView.vue'),
      props: (route) => ({
        projectId: route.params.projectId,
        evidenceId: route.query.evidenceId as string | undefined,
      }),
    },
    {
      path: '/projects/:projectId/assets',
      name: 'assets',
      component: () => import('@/views/AssetsView.vue'),
      props: true,
    },
    {
      path: '/projects/:projectId/evidences',
      name: 'evidences',
      component: () => import('@/views/EvidencesView.vue'),
      props: true,
    },
    {
      path: '/projects/:projectId/evidence-wizard',
      name: 'evidence-wizard',
      component: () => import('@/views/EvidenceWizardView.vue'),
      props: (route) => ({
        projectId: route.params.projectId,
        evidenceId: route.query.evidenceId as string | undefined,
      }),
    },
    {
      path: '/projects/:projectId/review',
      name: 'review',
      component: () => import('@/views/ReviewView.vue'),
      props: (route) => ({
        projectId: route.params.projectId,
        evidenceId: route.query.evidenceId as string | undefined,
      }),
    },
    {
      path: '/projects/:projectId/records',
      name: 'records',
      component: () => import('@/views/RecordsView.vue'),
      props: true,
    },
    {
      path: '/projects/:projectId/exports',
      name: 'exports',
      component: () => import('@/views/ExportCenterView.vue'),
      props: true,
    },
    {
      path: '/history-records',
      name: 'history-records',
      component: () => import('@/views/HistoryRecordsView.vue'),
    },
    {
      path: '/assessment-templates',
      name: 'assessment-templates',
      component: () => import('@/views/AssessmentTemplateView.vue'),
    },
    {
      path: '/guidance',
      name: 'guidance',
      component: () => import('@/views/GuidanceView.vue'),
    },
  ],
})

export default router
