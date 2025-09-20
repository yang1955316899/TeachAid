import { defineAsyncComponent } from 'vue'

// 动态注册管理员路由，避免破坏现有路由结构
export function setupAdminRoutes(router) {
  // 如果已存在，跳过
  if (router.hasRoute('Admin')) return

  router.addRoute({
    path: '/admin',
    name: 'Admin',
    component: defineAsyncComponent(() => import('@/views/admin/Layout.vue')),
    meta: {
      requiresAuth: true,
      role: 'admin',
      title: '管理员中心'
    },
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: defineAsyncComponent(() => import('@/views/admin/dashboard/index.vue')),
        meta: { title: '管理员仪表盘' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: defineAsyncComponent(() => import('@/views/admin/users/index.vue')),
        meta: { title: '用户管理' }
      },
      {
        path: 'users/create',
        name: 'AdminCreateUser',
        component: defineAsyncComponent(() => import('@/views/admin/users/create.vue')),
        meta: { title: '创建用户' }
      },
      {
        path: 'classes',
        name: 'AdminClasses',
        component: defineAsyncComponent(() => import('@/views/admin/classes/index.vue')),
        meta: { title: '班级管理' }
      },
      {
        path: 'classes/create',
        name: 'AdminCreateClass',
        component: defineAsyncComponent(() => import('@/views/admin/classes/create.vue')),
        meta: { title: '创建班级' }
      },
      {
        path: 'teaching-assignments',
        name: 'AdminTeachingAssignments',
        component: defineAsyncComponent(() => import('@/views/admin/teaching/index.vue')),
        meta: { title: '授课安排' }
      },
      {
        path: 'homeworks',
        name: 'AdminHomeworks',
        component: defineAsyncComponent(() => import('@/views/admin/homeworks/index.vue')),
        meta: { title: '作业管理' }
      },
      {
        path: 'questions',
        name: 'AdminQuestions',
        component: defineAsyncComponent(() => import('@/views/admin/questions/index.vue')),
        meta: { title: '题目管理' }
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: defineAsyncComponent(() => import('@/views/admin/settings/index.vue')),
        meta: { title: '系统设置' }
      },
      {
        path: 'permissions',
        name: 'AdminPermissions',
        component: defineAsyncComponent(() => import('@/views/admin/permissions/index.vue')),
        meta: { title: '权限管理' }
      },
      {
        path: 'analytics/overview',
        name: 'AdminAnalyticsOverview',
        component: defineAsyncComponent(() => import('@/views/admin/analytics/overview.vue')),
        meta: { title: '数据概览' }
      },
      {
        path: 'analytics/users',
        name: 'AdminAnalyticsUsers',
        component: defineAsyncComponent(() => import('@/views/admin/analytics/users.vue')),
        meta: { title: '用户分析' }
      },
      {
        path: 'analytics/content',
        name: 'AdminAnalyticsContent',
        component: defineAsyncComponent(() => import('@/views/admin/analytics/content.vue')),
        meta: { title: '内容分析' }
      },
      {
        path: 'profile',
        name: 'AdminProfile',
        // 复用教师的个人信息页面
        component: defineAsyncComponent(() => import('@/views/teacher/profile/index.vue')),
        meta: { title: '个人信息' }
      }
    ]
  })
}

