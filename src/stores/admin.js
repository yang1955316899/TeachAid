/**
 * 管理员状态管理
 */
import { defineStore } from 'pinia'
import adminApi from '@/api/admin'

export const useAdminStore = defineStore('admin', {
  state: () => ({
    // 系统统计
    systemStats: {
      total_users: 0,
      total_teachers: 0,
      total_students: 0,
      total_admins: 0,
      total_classes: 0,
      total_questions: 0,
      total_homeworks: 0,
      active_users_today: 0,
      active_users_week: 0,
      recent_logins: []
    },

    // 用户管理
    users: {
      items: [],
      total: 0,
      loading: false
    },

    // 班级管理
    classes: {
      items: [],
      total: 0,
      loading: false
    },

    // 作业管理
    homeworks: {
      items: [],
      total: 0,
      loading: false
    },

    // 题目管理
    questions: {
      items: [],
      total: 0,
      loading: false
    },

    // 系统设置
    systemSettings: {
      items: [],
      total: 0,
      loading: false,
      categories: []
    },

    // 权限管理
    permissions: {
      items: [],
      total: 0,
      loading: false
    },

    // 数据分析
    analytics: {
      overview: null,
      userAnalytics: null,
      contentAnalytics: null,
      loading: false
    }
  }),

  getters: {
    // 获取用户角色统计
    userRoleStats: (state) => {
      return {
        teachers: state.systemStats.total_teachers,
        students: state.systemStats.total_students,
        admins: state.systemStats.total_admins
      }
    },

    // 获取活跃用户比例
    activeUserRates: (state) => {
      const total = state.systemStats.total_users
      return {
        today: total ? ((state.systemStats.active_users_today / total) * 100).toFixed(2) : 0,
        week: total ? ((state.systemStats.active_users_week / total) * 100).toFixed(2) : 0
      }
    }
  },

  actions: {
    // ============ 系统统计 ============
    async fetchSystemStats() {
      try {
        const response = await adminApi.getSystemStats()
        if (response.success) {
          this.systemStats = response.data
        }
        return response
      } catch (error) {
        console.error('获取系统统计失败:', error)
        throw error
      }
    },

    // ============ 用户管理 ============
    async fetchUsers(params = {}) {
      this.users.loading = true
      try {
        const response = await adminApi.getUsers(params)

        // 处理两种可能的响应格式
        if (response.success && response.data) {
          // 新格式：包装在ResponseModel中
          this.users.items = response.data.items
          this.users.total = response.data.total
        } else if (response.items) {
          // 旧格式：直接的PageResponseModel
          this.users.items = response.items
          this.users.total = response.total
        }

        return response
      } catch (error) {
        console.error('获取用户列表失败:', error)
        throw error
      } finally {
        this.users.loading = false
      }
    },

    async createUser(userData) {
      try {
        const response = await adminApi.createUser(userData)
        if (response.success) {
          // 重新获取用户列表
          await this.fetchUsers()
          // 更新统计
          await this.fetchSystemStats()
        }
        return response
      } catch (error) {
        console.error('创建用户失败:', error)
        throw error
      }
    },

    async updateUser(userId, userData) {
      try {
        const response = await adminApi.updateUser(userId, userData)
        if (response.success) {
          // 更新本地数据
          const index = this.users.items.findIndex(user => user.user_id === userId)
          if (index !== -1) {
            Object.assign(this.users.items[index], userData)
          }
        }
        return response
      } catch (error) {
        console.error('更新用户失败:', error)
        throw error
      }
    },

    async deleteUser(userId) {
      try {
        const response = await adminApi.deleteUser(userId)
        if (response.success) {
          // 从本地列表移除
          this.users.items = this.users.items.filter(user => user.user_id !== userId)
          this.users.total -= 1
          // 更新统计
          await this.fetchSystemStats()
        }
        return response
      } catch (error) {
        console.error('删除用户失败:', error)
        throw error
      }
    },

    async resetUserPassword(userId, newPassword) {
      try {
        const response = await adminApi.resetUserPassword(userId, { new_password: newPassword })
        return response
      } catch (error) {
        console.error('重置密码失败:', error)
        throw error
      }
    },

    // ============ 班级管理 ============
    async fetchClasses(params = {}) {
      this.classes.loading = true
      try {
        const response = await adminApi.getClasses(params)
        if (response.success) {
          this.classes.items = response.data.items
          this.classes.total = response.data.total
        }
        return response
      } catch (error) {
        console.error('获取班级列表失败:', error)
        throw error
      } finally {
        this.classes.loading = false
      }
    },

    async createClass(classData) {
      try {
        const response = await adminApi.createClass(classData)
        if (response.success) {
          await this.fetchClasses()
          await this.fetchSystemStats()
        }
        return response
      } catch (error) {
        console.error('创建班级失败:', error)
        throw error
      }
    },

    async updateClass(classId, classData) {
      try {
        const response = await adminApi.updateClass(classId, classData)
        if (response.success) {
          const index = this.classes.items.findIndex(cls => cls.id === classId)
          if (index !== -1) {
            Object.assign(this.classes.items[index], classData)
          }
        }
        return response
      } catch (error) {
        console.error('更新班级失败:', error)
        throw error
      }
    },

    async deleteClass(classId) {
      try {
        const response = await adminApi.deleteClass(classId)
        if (response.success) {
          this.classes.items = this.classes.items.filter(cls => cls.id !== classId)
          this.classes.total -= 1
          await this.fetchSystemStats()
        }
        return response
      } catch (error) {
        console.error('删除班级失败:', error)
        throw error
      }
    },

    // ============ 作业管理 ============
    async fetchHomeworks(params = {}) {
      this.homeworks.loading = true
      try {
        const response = await adminApi.getHomeworks(params)
        if (response.success) {
          this.homeworks.items = response.data.items
          this.homeworks.total = response.data.total
        }
        return response
      } catch (error) {
        console.error('获取作业列表失败:', error)
        throw error
      } finally {
        this.homeworks.loading = false
      }
    },

    async publishHomework(homeworkId) {
      try {
        const response = await adminApi.publishHomework(homeworkId)
        if (response.success) {
          const index = this.homeworks.items.findIndex(hw => hw.id === homeworkId)
          if (index !== -1) {
            this.homeworks.items[index].is_published = true
          }
        }
        return response
      } catch (error) {
        console.error('发布作业失败:', error)
        throw error
      }
    },

    async unpublishHomework(homeworkId) {
      try {
        const response = await adminApi.unpublishHomework(homeworkId)
        if (response.success) {
          const index = this.homeworks.items.findIndex(hw => hw.id === homeworkId)
          if (index !== -1) {
            this.homeworks.items[index].is_published = false
          }
        }
        return response
      } catch (error) {
        console.error('撤回作业失败:', error)
        throw error
      }
    },

    // ============ 题目管理 ============
    async fetchQuestions(params = {}) {
      this.questions.loading = true
      try {
        const response = await adminApi.getQuestions(params)
        if (response.success) {
          this.questions.items = response.data.items
          this.questions.total = response.data.total
        }
        return response
      } catch (error) {
        console.error('获取题目列表失败:', error)
        throw error
      } finally {
        this.questions.loading = false
      }
    },

    async updateQuestionStatus(questionId, isActive) {
      try {
        const response = await adminApi.updateQuestionStatus(questionId, isActive)
        if (response.success) {
          const index = this.questions.items.findIndex(q => q.id === questionId)
          if (index !== -1) {
            this.questions.items[index].is_active = isActive
          }
        }
        return response
      } catch (error) {
        console.error('更新题目状态失败:', error)
        throw error
      }
    },

    async updateQuestionPublicity(questionId, isPublic) {
      try {
        const response = await adminApi.updateQuestionPublicity(questionId, isPublic)
        if (response.success) {
          const index = this.questions.items.findIndex(q => q.id === questionId)
          if (index !== -1) {
            this.questions.items[index].is_public = isPublic
          }
        }
        return response
      } catch (error) {
        console.error('更新题目公开状态失败:', error)
        throw error
      }
    },

    async deleteQuestion(questionId) {
      try {
        const response = await adminApi.deleteQuestion(questionId)
        if (response.success) {
          this.questions.items = this.questions.items.filter(q => q.id !== questionId)
          this.questions.total -= 1
          await this.fetchSystemStats()
        }
        return response
      } catch (error) {
        console.error('删除题目失败:', error)
        throw error
      }
    },

    // ============ 系统设置 ============
    async fetchSystemSettings(params = {}) {
      this.systemSettings.loading = true
      try {
        const response = await adminApi.getSystemSettings(params)
        if (response.success) {
          this.systemSettings.items = response.data.items
          this.systemSettings.total = response.data.total
        }
        return response
      } catch (error) {
        console.error('获取系统设置失败:', error)
        throw error
      } finally {
        this.systemSettings.loading = false
      }
    },

    async fetchSettingCategories() {
      try {
        const response = await adminApi.getSettingCategories()
        if (response.success) {
          this.systemSettings.categories = response.data
        }
        return response
      } catch (error) {
        console.error('获取设置分类失败:', error)
        throw error
      }
    },

    // ============ 数据分析 ============
    async fetchAnalyticsOverview(params = {}) {
      this.analytics.loading = true
      try {
        const response = await adminApi.getAnalyticsOverview(params)
        if (response.success) {
          this.analytics.overview = response.data
        }
        return response
      } catch (error) {
        console.error('获取数据分析概览失败:', error)
        throw error
      } finally {
        this.analytics.loading = false
      }
    },

    async fetchUserAnalytics(params = {}) {
      try {
        const response = await adminApi.getUserAnalytics(params)
        if (response.success) {
          this.analytics.userAnalytics = response.data
        }
        return response
      } catch (error) {
        console.error('获取用户分析失败:', error)
        throw error
      }
    },

    async fetchContentAnalytics(params = {}) {
      try {
        const response = await adminApi.getContentAnalytics(params)
        if (response.success) {
          this.analytics.contentAnalytics = response.data
        }
        return response
      } catch (error) {
        console.error('获取内容分析失败:', error)
        throw error
      }
    },

    async exportAnalyticsData(format = 'csv', params = {}) {
      try {
        const response = await adminApi.exportAnalyticsData({
          format,
          ...params
        })

        // 创建下载链接
        const blob = new Blob([response], {
          type: format === 'json' ? 'application/json' : 'text/csv'
        })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `analytics_${new Date().toISOString().split('T')[0]}.${format}`
        link.click()
        window.URL.revokeObjectURL(url)

        return { success: true, message: '数据导出成功' }
      } catch (error) {
        console.error('导出数据失败:', error)
        throw error
      }
    }
  }
})