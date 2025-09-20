import axios from 'axios'
import { message } from 'ant-design-vue'

// 创建 axios 实例
const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})

// 刷新令牌并发控制
let isRefreshing = false
let failedQueue = []
const processQueue = (error, token = null) => {
  failedQueue.forEach((p) => {
    if (error) p.reject(error)
    else p.resolve(token)
  })
  failedQueue = []
}

// 请求拦截器：带上 token
http.interceptors.request.use(
  async (config) => {
    const token = localStorage.getItem('token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一数据/错误处理
http.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const originalRequest = error.config || {}
    const status = error.response?.status
    const data = error.response?.data

    // 401：尝试刷新令牌
    if (status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return http(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true
      try {
        const refreshToken = localStorage.getItem('refreshToken')
        if (refreshToken) {
          const res = await axios.post('/api/auth/refresh', { refresh_token: refreshToken })
          const { access_token } = res.data.data
          localStorage.setItem('token', access_token)
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          processQueue(null, access_token)
          return http(originalRequest)
        }
      } catch (refreshError) {
        processQueue(refreshError, null)
        localStorage.removeItem('token')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('user')
        message.error('登录状态已过期，请重新登录')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 其他错误：显示服务端返回的 message/detail
    try {
      const serverMessage = data?.detail || data?.message || data?.error?.message
      if (status === 423) {
        message.error(serverMessage || '账户已锁定')
      } else if (status && status >= 400) {
        message.error(serverMessage || '请求失败')
      }
      console.error('HTTP请求错误:', serverMessage || error.message)
    } catch (_) {
      // 忽略解析异常
    }

    return Promise.reject(error)
  }
)

export default http

