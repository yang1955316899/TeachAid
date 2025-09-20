import { useAuthStore } from '@/stores/auth'
import { message } from 'ant-design-vue'

// 路由守卫配置
export function setupRouterGuards(router) {
  let authInitialized = false

  router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()
    const requiresAuth = to.matched.some((r) => r.meta.requiresAuth)
    const requiresRole = to.meta.role

    // 初始化一次认证状态
    if (!authInitialized) {
      try {
        await authStore.initAuth()
      } catch (e) {
        // ignore, 后续逻辑会处理
      }
      authInitialized = true
    }

    // 需要登录但未登录
    if (requiresAuth && !authStore.isLoggedIn) {
      if (from.path !== '/login') message.warning('请先登录')
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }

    // 角色校验
    if (requiresRole && authStore.isLoggedIn) {
      const { allowed, redirectPath, message: tip } = await checkRolePermission(authStore, requiresRole)
      if (!allowed) {
        if (tip) message.warning(tip)
        next(redirectPath)
        return
      }
    }

    // 已登录访问登录页 => 跳转默认首页
    if (to.path === '/login' && authStore.isLoggedIn) {
      next(getDefaultRedirectPath(authStore))
      return
    }

    next()
  })

  router.afterEach(() => {
    const authStore = useAuthStore()
    if (authStore.loading) authStore.loading = false
  })

  router.onError((err) => {
    console.error('路由错误:', err)
    const authStore = useAuthStore()
    authStore.loading = false
    if (err?.message?.includes('authentication') || err?.message?.includes('authorization')) {
      message.error('认证失败，请重新登录')
      window.location.href = '/login'
    }
  })
}

async function checkRolePermission(authStore, requiredRole) {
  const role = authStore.userRole
  switch (requiredRole) {
    case 'teacher':
      if (!authStore.isTeacher) {
        return {
          allowed: false,
          message: '需要教师权限',
          redirectPath: role === 'admin' ? '/admin/dashboard' : (authStore.isStudent ? '/student/dashboard' : '/login')
        }
      }
      break
    case 'student':
      if (!authStore.isStudent) {
        return {
          allowed: false,
          message: '需要学生权限',
          redirectPath: role === 'admin' ? '/admin/dashboard' : (authStore.isTeacher ? '/teacher/dashboard' : '/login')
        }
      }
      break
    case 'admin':
      if (role !== 'admin') {
        return {
          allowed: false,
          message: '需要管理员权限',
          redirectPath: authStore.isTeacher ? '/teacher/dashboard' : '/student/dashboard'
        }
      }
      break
  }
  return { allowed: true }
}

function getDefaultRedirectPath(authStore) {
  if (authStore.isTeacher) return '/teacher/dashboard'
  if (authStore.isStudent) return '/student/dashboard'
  if (authStore.userRole === 'admin') return '/admin/dashboard'
  return '/login'
}

