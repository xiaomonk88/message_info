import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  { path: '/register', component: () => import('@/views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '仪表盘' } },
      { path: 'm/:moduleId(\\d+)', component: () => import('@/views/front/ModuleRecords.vue'), meta: { title: '记录管理' } },
      { path: 'admin/categories', component: () => import('@/views/admin/Categories.vue'), meta: { title: '分类管理', admin: true } },
      { path: 'admin/fields', component: () => import('@/views/admin/Fields.vue'), meta: { title: '字段管理', admin: true } },
      { path: 'admin/modules', component: () => import('@/views/admin/Modules.vue'), meta: { title: '板块管理', admin: true } },
      { path: 'admin/users', component: () => import('@/views/admin/Users.vue'), meta: { title: '用户管理', admin: true } },
      { path: 'admin/backups', component: () => import('@/views/admin/Backups.vue'), meta: { title: '数据备份', admin: true } },
      { path: 'admin/audit', component: () => import('@/views/admin/Audit.vue'), meta: { title: '操作日志', admin: true } },
      { path: 'admin/account', component: () => import('@/views/admin/Account.vue'), meta: { title: '账号安全' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

let meChecked = false

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) return auth.token ? '/' : true
  if (!auth.token) return '/login'
  // 每次打开页面先向服务端确认一次身份与角色
  if (!meChecked) {
    meChecked = true
    try {
      await auth.fetchMe()
    } catch {
      // 401 由 http 拦截器统一跳转登录
    }
  }
  // 管理页面仅管理员可进（后端同样会拦截，这里只是体验层）
  if (to.meta.admin && !auth.isAdmin) return '/dashboard'
  return true
})

export default router
