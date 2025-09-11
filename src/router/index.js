import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/teacher',
    name: 'Teacher',
    component: () => import('@/views/teacher/Layout.vue'),
    children: [
      {
        path: 'dashboard',
        name: 'TeacherDashboard',
        component: () => import('@/views/teacher/dashboard/index.vue')
      },
      {
        path: 'question',
        name: 'QuestionManage',
        component: () => import('@/views/teacher/question/index.vue')
      },
      {
        path: 'homework',
        name: 'HomeworkManage',
        component: () => import('@/views/teacher/homework/index.vue')
      },
      {
        path: 'class',
        name: 'ClassManage',
        component: () => import('@/views/teacher/class/index.vue')
      },
      {
        path: 'prompt',
        name: 'PromptManage',
        component: () => import('@/views/teacher/prompt/index.vue')
      }
    ]
  },
  {
    path: '/student',
    name: 'Student',
    component: () => import('@/views/student/Layout.vue'),
    children: [
      {
        path: 'dashboard',
        name: 'StudentDashboard',
        component: () => import('@/views/student/dashboard/index.vue')
      },
      {
        path: 'homework',
        name: 'StudentHomework',
        component: () => import('@/views/student/homework/index.vue')
      },
      {
        path: 'study',
        name: 'StudentStudy',
        component: () => import('@/views/student/study/index.vue')
      },
      {
        path: 'progress',
        name: 'StudentProgress',
        component: () => import('@/views/student/progress/index.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router