/**
 * 增强认证状态管理 - 实现完整的认证流程
 */
import { defineStore } from 'pinia'
import http from '@/utils/http'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // 用户信息
    user: null,
    token: localStorage.getItem('token'),
    refreshToken: localStorage.getItem('refreshToken'),
    isAuthenticated: false,
    permissions: [],
    
    // 令牌状态
    tokenExpiry: null,
    isRefreshing: false,
    
    // 加载状态
    loading: false,
    error: null
  }),
  
  getters: {
    // 基础状态
    isLoggedIn: (state) => !!state.token && state.isAuthenticated,
    userRole: (state) => state.user?.user_role || state.user?.role || (state.isLoggedIn ? 'guest' : null),
    userId: (state) => state.user?.user_id || state.user?.id,
    userName: (state) => state.user?.user_name || state.user?.username,
    userFullName: (state) => state.user?.user_full_name || state.user?.full_name,
    userEmail: (state) => state.user?.user_email || state.user?.email,
    
    // 角色检查
    isTeacher: (state) => state.user?.user_role === 'teacher' || state.user?.role === 'teacher',
    isStudent: (state) => state.user?.user_role === 'student' || state.user?.role === 'student',
    isAdmin: (state) => state.user?.user_role === 'admin' || state.user?.role === 'admin',
    
    
    // 令牌状态
    isTokenExpired: (state) => {
      if (!state.tokenExpiry) return false
      return new Date() > new Date(state.tokenExpiry)
    },
    
    // 权限检查
    hasPermission: (state) => (permission) => {
      return state.permissions.includes(permission)
    },
    
    // 用户显示信息
    displayName: (state) => {
      return state.user?.user_full_name || state.user?.full_name || state.user?.user_name || state.user?.username || '未知用户'
    }
  },
  
  actions: {
    /**
     * 初始化认证状态
     */
    async initAuth() {
      try {
        const token = localStorage.getItem('token')
        const user = localStorage.getItem('user')
        const refreshToken = localStorage.getItem('refreshToken')
        
        if (token && user) {
          this.token = token
          this.refreshToken = refreshToken
          this.user = JSON.parse(user)
          this.isAuthenticated = true
          
          // 验证令牌有效性
          await this.validateToken()
        }
      } catch (error) {
        console.error('初始化认证失败:', error)
        this.clearAuth()
      }
    },
    
    /**
     * 用户登录
     */
    async login(credentials) {
      this.loading = true
      this.error = null
      
      try {
        const response = await authApi.login(credentials)
        
        if (response.access_token) {
          // 设置认证状态
          this.token = response.access_token
          this.refreshToken = response.refresh_token
          this.user = response.user
          this.isAuthenticated = true
          
          // 计算令牌过期时间
          this.tokenExpiry = new Date(Date.now() + response.expires_in * 1000)
          
          // 持久化到本地存储
          this.persistAuth()
          
          // 获取用户权限
          await this.fetchUserPermissions()
          
          return { success: true, data: response }
        } else {
          throw new Error(response.message || '登录失败')
        }
      } catch (error) {
        this.error = error.message || '登录失败'
        console.error('登录失败:', error)
        return { success: false, message: this.error }
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 用户注册
     */
    async register(userData) {
      this.loading = true
      this.error = null
      
      try {
        const response = await authApi.register(userData)
        
        if (response.success) {
          // 注册成功后自动登录
          await this.login({
            username: userData.username,
            password: userData.password
          })
        }
        
        return response
      } catch (error) {
        this.error = error.message || '注册失败'
        console.error('注册失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 刷新访问令牌
     */
    async refreshAccessToken() {
      if (this.isRefreshing || !this.refreshToken) {
        return false
      }
      
      this.isRefreshing = true
      
      try {
        const response = await authApi.refreshToken(this.refreshToken)
        
        if (response && response.success && response.data && response.data.access_token) {
          this.token = response.data.access_token
          this.tokenExpiry = new Date(Date.now() + response.data.expires_in * 1000)
          
          // 更新本地存储
          localStorage.setItem('token', this.token)
          
          return true
        } else {
          // 刷新失败，清除认证状态
          this.clearAuth()
          return false
        }
      } catch (error) {
        console.error('令牌刷新失败:', error)
        this.clearAuth()
        return false
      } finally {
        this.isRefreshing = false
      }
    },
    
    /**
     * 验证令牌有效性
     */
    async validateToken() {
      try {
        // 尝试获取用户信息来验证令牌
        await this.fetchUserProfile()
        return true
      } catch (error) {
        console.error('令牌验证失败:', error)
        
        // 尝试刷新令牌
        if (await this.refreshAccessToken()) {
          return true
        }
        
        this.clearAuth()
        return false
      }
    },
    
    /**
     * 获取用户信息
     */
    async fetchUserProfile() {
      try {
        const response = await authApi.getProfile()
        // getProfile 返回的就是用户对象（非 BaseResponse 包裹）
        this.user = response
        this.isAuthenticated = true
        
        // 更新本地存储
        localStorage.setItem('user', JSON.stringify(response))
        
        return response
      } catch (error) {
        console.error('获取用户信息失败:', error)
        throw error
      }
    },
    
    /**
     * 获取用户权限
     */
    async fetchUserPermissions() {
      try {
        const response = await authApi.getPermissions()
        // getPermissions 返回 BaseResponse，权限在 data.permissions 中
        this.permissions = (response && response.data && Array.isArray(response.data.permissions))
          ? response.data.permissions
          : []
        return this.permissions
      } catch (error) {
        console.error('获取用户权限失败:', error)
        this.permissions = []
        throw error
      }
    },
    
    /**
     * 检查认证状态
     */
    async checkAuthStatus() {
      try {
        const response = await authApi.checkAuth()
        // checkAuth 返回 BaseResponse，认证标志在 data.authenticated
        return !!(response && response.data && response.data.authenticated)
      } catch (error) {
        return false
      }
    },
    
    /**
     * 修改密码
     */
    async changePassword(oldPassword, newPassword) {
      this.loading = true
      this.error = null
      
      try {
        const response = await authApi.changePassword(oldPassword, newPassword)
        
        if (response.success) {
          // 密码修改成功，清除认证状态要求重新登录
          this.clearAuth()
        }
        
        return response
      } catch (error) {
        this.error = error.message || '密码修改失败'
        console.error('修改密码失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 用户登出
     */
    async logout() {
      this.loading = true
      
      try {
        // 调用登出API
        await authApi.logout()
      } catch (error) {
        console.error('登出API调用失败:', error)
      } finally {
        this.clearAuth()
        this.loading = false
        
        // 跳转到登录页
        window.location.href = '/login'
      }
    },
    
    /**
     * 清除认证状态
     */
    clearAuth() {
      this.user = null
      this.token = null
      this.refreshToken = null
      this.isAuthenticated = false
      this.permissions = []
      this.tokenExpiry = null
      this.error = null
      
      // 清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('user')
    },
    
    /**
     * 持久化认证状态
     */
    persistAuth() {
      localStorage.setItem('token', this.token)
      localStorage.setItem('refreshToken', this.refreshToken)
      localStorage.setItem('user', JSON.stringify(this.user))
    },
    
    /**
     * 检查权限（异步）
     */
    async ensurePermission(permission) {
      if (!this.isAuthenticated) {
        return false
      }
      
      if (this.permissions.length === 0) {
        await this.fetchUserPermissions()
      }
      
      return this.hasPermission(permission)
    },
    
    /**
     * 检查角色
     */
    hasRole(role) {
      return this.userRole === role
    },
    
    /**
     * 获取用户头像
     */
    getUserAvatar() {
      // 可以根据用户信息生成头像URL
      if (this.user?.email) {
        return `https://ui-avatars.com/api/?name=${encodeURIComponent(this.displayName)}&background=3b82f6&color=fff`
      }
      return null
    },
    
    /**
     * 获取用户状态文本
     */
    getUserStatusText() {
      if (this.isAdmin) {
        return '管理员'
      }
      if (this.isTeacher) {
        return '教师'
      }
      if (this.isStudent) {
        return '学生'
      }
      return '访客'
    }
  }
})
