import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    isAuthenticated: false
  }),
  
  getters: {
    userRole: (state) => state.user?.role || null,
    userName: (state) => state.user?.name || '',
    isTeacher: (state) => state.user?.role === 'teacher',
    isStudent: (state) => state.user?.role === 'student'
  },
  
  actions: {
    async login(credentials) {
      try {
        // 模拟登录API调用
        const response = await this.mockLogin(credentials)
        
        this.user = response.user
        this.token = response.token
        this.isAuthenticated = true
        
        // 保存到本地存储
        localStorage.setItem('token', response.token)
        localStorage.setItem('user', JSON.stringify(response.user))
        
        return response
      } catch (error) {
        console.error('登录失败:', error)
        throw error
      }
    },
    
    async logout() {
      this.user = null
      this.token = null
      this.isAuthenticated = false
      
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
    
    async checkAuth() {
      const token = localStorage.getItem('token')
      const user = localStorage.getItem('user')
      
      if (token && user) {
        this.token = token
        this.user = JSON.parse(user)
        this.isAuthenticated = true
      }
    },
    
    // 模拟登录API
    async mockLogin(credentials) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          if (credentials.username && credentials.password) {
            const isTeacher = credentials.username.includes('teacher')
            resolve({
              user: {
                id: '1',
                name: isTeacher ? '张老师' : '李同学',
                username: credentials.username,
                role: isTeacher ? 'teacher' : 'student'
              },
              token: 'mock-jwt-token-' + Date.now()
            })
          } else {
            reject(new Error('用户名或密码错误'))
          }
        }, 1000)
      })
    }
  }
})