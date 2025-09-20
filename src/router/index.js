import { createRouter, createWebHistory } from 'vue-router'
import { setupRouterGuards } from './guards'
import { setupAdminRoutes } from './routes_admin'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/teacher',
    name: 'Teacher',
    component: () => import('@/views/teacher/Layout.vue'),
    meta: { 
      requiresAuth: true, 
      role: 'teacher',
      title: '教师工作台'
    },
    children: [
      {
        path: 'dashboard',
        name: 'TeacherDashboard',
        component: () => import('@/views/teacher/dashboard/index.vue'),
        meta: { title: '教师仪表板' }
      },
      {
        path: 'question',
        name: 'QuestionManage',
        component: () => import('@/views/teacher/question/index.vue'),
        meta: { title: '题目管理' }
      },
      {
        path: 'homework',
        name: 'HomeworkManage',
        component: () => import('@/views/teacher/homework/index.vue'),
        meta: { title: '作业管理' }
      },
      {
        path: 'class',
        name: 'ClassManage',
        component: () => import('@/views/teacher/class/index.vue'),
        meta: { title: '班级管理' }
      },
      {
        path: 'teaching',
        name: 'TeachingManage',
        component: () => import('@/views/teacher/teaching/index.vue'),
        meta: { title: '授课关系管理' }
      },
      {
        path: 'prompt',
        name: 'PromptManage',
        component: () => import('@/views/teacher/prompt/index.vue'),
        meta: { title: '提示词管理' }
      },
      {
        path: 'profile',
        name: 'TeacherProfile',
        component: () => import('@/views/teacher/profile/index.vue'),
        meta: { title: '个人信息' }
      }
    ]
  },
  {
    path: '/student',
    name: 'Student',
    component: () => import('@/views/student/Layout.vue'),
    meta: { 
      requiresAuth: true, 
      role: 'student',
      title: '学生中心'
    },
    children: [
      {
        path: 'dashboard',
        name: 'StudentDashboard',
        component: () => import('@/views/student/dashboard/index.vue'),
        meta: { title: '学生仪表板' }
      },
      {
        path: 'homework',
        name: 'StudentHomework',
        component: () => import('@/views/student/homework/index.vue'),
        meta: { title: '我的作业' }
      },
      {
        path: 'study',
        name: 'StudentStudy',
        component: () => import('@/views/student/study/index.vue'),
        meta: { title: '学习中心' }
      },
      {
        path: 'progress',
        name: 'StudentProgress',
        component: () => import('@/views/student/progress/index.vue'),
        meta: { title: '学习进度' }
      },
      {
        path: 'notes',
        name: 'StudentNotes',
        component: () => import('@/views/student/notes/index.vue'),
        meta: { title: '我的笔记' }
      },
      {
        path: 'profile',
        name: 'StudentProfile',
        component: () => import('@/views/student/profile/index.vue'),
        meta: { title: '个人信息' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 设置路由守卫
setupRouterGuards(router)

// 动态注册管理员路由
setupAdminRoutes(router)

export default router
