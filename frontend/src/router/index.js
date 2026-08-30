import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '拧紧质量监控大屏', icon: 'Monitor' },
  },
  {
    path: '/detection',
    name: 'detection',
    component: () => import('../views/Detection.vue'),
    meta: { title: '质量检测分析', icon: 'DataAnalysis' },
  },
  {
    path: '/traceability',
    name: 'traceability',
    component: () => import('../views/Traceability.vue'),
    meta: { title: '工艺追溯查询', icon: 'Search' },
  },
  {
    path: '/optimization',
    name: 'optimization',
    component: () => import('../views/Optimization.vue'),
    meta: { title: '工艺参数优化', icon: 'TrendCharts' },
  },
  {
    path: '/data',
    name: 'data',
    component: () => import('../views/DataManage.vue'),
    meta: { title: '基础数据管理', icon: 'Setting' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
