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
      path: '/template-rules',
      name: 'template-rules',
      component: () => import('@/views/TemplateRulesView.vue'),
    },
  ],
})

export default router
