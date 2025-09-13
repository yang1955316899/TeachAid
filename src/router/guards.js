import { useAuthStore } from '@/stores/auth'
import { message } from 'ant-design-vue'

/**
 * 路由守卫配置
 */
export function setupRouterGuards(router) {
  let authInitialized = false

  router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
    const requiresRole = to.meta.role

    // 初始化认证状态（只在第一次路由时执行）
    if (!authInitialized) {
      try {
        await authStore.initAuth()
        authInitialized = true
      } catch (error) {
        console.error('认证初始化失败:', error)
        // 初始化失败时继续，让路由守卫处理认证逻辑
      }
    }

    // 等待初始化完成
    if (authStore.loading) {
      // 显示加载状态并等待
      await new Promise(resolve => {
        const checkLoading = () => {
          if (!authStore.loading) {
            resolve()
          } else {
            setTimeout(checkLoading, 50)
          }
        }
        checkLoading()
      })
    }

    // 检查认证状态
    if (requiresAuth && !authStore.isLoggedIn) {
      // 需要认证但未登录，跳转登录页
      if (from.path !== '/login') {
        message.warning('请先登录')
      }
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }

    // 检查角色权限
    if (requiresRole && authStore.isLoggedIn) {
      const hasPermission = await checkRolePermission(authStore, requiresRole, to.fullPath)
      
      if (!hasPermission.allowed) {
        message.warning(hasPermission.message)
        next(hasPermission.redirectPath)
        return
      }
    }

    // 如果是登录页且已登录，跳转到对应首页
    if (to.path === '/login' && authStore.isLoggedIn) {
      const redirectPath = getDefaultRedirectPath(authStore)
      // 检查是否会造成循环重定向
      if (redirectPath !== to.path && redirectPath !== from.path) {
        next(redirectPath)
        return
      }
    }

    next()
  })

  router.afterEach((to) => {
    // 设置页面标题
    document.title = to.meta.title || 'TeachAid - AI辅助教学平台'
    
    // 隐藏加载状态
    const authStore = useAuthStore()
    if (authStore.loading) {
      authStore.loading = false
    }
  })

  // 路由错误处理
  router.onError((error) => {
    console.error('路由错误:', error)
    const authStore = useAuthStore()
    authStore.loading = false
    
    // 如果是认证相关错误，跳转到登录页
    if (error.message?.includes('authentication') || error.message?.includes('authorization')) {
      message.error('认证失败，请重新登录')
      window.location.href = '/login'
    }
  })
}

/**
 * 检查角色权限
 */
async function checkRolePermission(authStore, requiredRole, currentPath) {
  const userRole = authStore.userRole

  // 检查特定角色权限
  switch (requiredRole) {
    case 'teacher':
      if (!authStore.isTeacher) {
        return {
          allowed: false,
          message: '需要教师权限',
          redirectPath: authStore.isStudent ? '/student/dashboard' : '/login'
        }
      }
      break

    case 'student':
      if (!authStore.isStudent) {
        return {
          allowed: false,
          message: '需要学生权限',
          redirectPath: authStore.isTeacher ? '/teacher/dashboard' : '/login'
        }
      }
      break

    case 'admin':
      if (userRole !== 'admin') {
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

/**
 * 获取默认重定向路径
 */
function getDefaultRedirectPath(authStore) {
  const role = authStore.userRole
  console.log('getDefaultRedirectPath - userRole:', role, 'isTeacher:', authStore.isTeacher, 'isStudent:', authStore.isStudent)
  
  if (authStore.isTeacher) {
    return '/teacher/dashboard'
  } else if (authStore.isStudent) {
    return '/student/dashboard'
  } else if (role === 'admin') {
    return '/admin/dashboard'
  } else {
    console.warn('未知用户角色:', role)
    return '/login'
  }
}