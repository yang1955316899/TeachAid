import axios from 'axios'

// 创建axios实例
const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 刷新令牌标志，防止并发刷新
let isRefreshing = false
let failedQueue = []

// 处理失败的队列
const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// 请求拦截器
http.interceptors.request.use(
  async (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
http.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    const originalRequest = error.config

    // 处理401错误（令牌过期）
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // 如果正在刷新令牌，将请求加入队列
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return http(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        // 尝试刷新令牌
        const refreshToken = localStorage.getItem('refreshToken')
        if (refreshToken) {
          const response = await axios.post('/api/auth/refresh', {
            refresh_token: refreshToken
          })

          const { access_token } = response.data.data
          
          // 更新本地存储
          localStorage.setItem('token', access_token)
          
          // 更新请求头
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          
          // 处理队列中的请求
          processQueue(null, access_token)
          
          // 重试原始请求
          return http(originalRequest)
        }
      } catch (refreshError) {
        // 刷新失败，清除认证状态并跳转登录页
        processQueue(refreshError, null)
        localStorage.removeItem('token')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 处理其他错误
    const errorMessage = error.response?.data?.detail || error.message || '请求失败'
    console.error('HTTP请求错误:', errorMessage)
    
    return Promise.reject(error)
  }
)

export default http