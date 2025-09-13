import http from '@/utils/http'

/**
 * 认证相关API
 */
export const authApi = {
  /**
   * 用户注册
   */
  register(data) {
    return http.post('/auth/register', data)
  },

  /**
   * 用户登录
   */
  login(data) {
    return http.post('/auth/login', data)
  },

  /**
   * 刷新令牌
   */
  refreshToken(refreshToken) {
    return http.post('/auth/refresh', { refresh_token: refreshToken })
  },

  /**
   * 获取用户信息
   */
  getProfile() {
    return http.get('/auth/profile')
  },

  /**
   * 获取用户权限
   */
  getPermissions() {
    return http.get('/auth/permissions')
  },

  /**
   * 修改密码
   */
  changePassword(data) {
    return http.post('/auth/change-password', data)
  },

  /**
   * 用户登出
   */
  logout() {
    return http.post('/auth/logout')
  },

  /**
   * 检查认证状态
   */
  checkAuth() {
    return http.get('/auth/check-auth')
  }
}