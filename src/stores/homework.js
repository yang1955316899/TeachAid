import { defineStore } from 'pinia'
import { homeworkApi } from '@/api/homework'
import { message } from 'ant-design-vue'

export const useHomeworkStore = defineStore('homework', {
  state: () => ({
    homeworks: [],
    studentHomeworks: [],
    currentHomework: null,
    currentStudentHomework: null,
    loading: false,
    pagination: {
      current: 1,
      pageSize: 10,
      total: 0,
      pages: 0
    },
    studentPagination: {
      current: 1,
      pageSize: 10,
      total: 0,
      pages: 0
    }
  }),
  
  getters: {
    homeworkCount: (state) => state.homeworks.length,
    studentHomeworkCount: (state) => state.studentHomeworks.length,
    homeworkByClass: (state) => {
      return (className) => state.homeworks.filter(h => h.class_name === className)
    },
    homeworkByStatus: (state) => {
      return (status) => state.studentHomeworks.filter(h => h.status === status)
    },
    homeworkOptions: (state) => {
      return state.studentHomeworks.map(homework => ({
        label: homework.title,
        value: homework.id,
        subject: homework.subject_name,
        status: homework.status
      }))
    }
  },
  
  actions: {
    /**
     * 获取作业列表
     */
    async fetchHomeworks(params = {}) {
      this.loading = true
      try {
        const response = await homeworkApi.getHomeworks(params)
        // 兼容 BaseResponse 与直接分页响应两种结构
        let items, page, size, total, pages, success = true
        if (response && Object.prototype.hasOwnProperty.call(response, 'success')) {
          success = !!response.success
          if (!success) throw new Error(response.message || '获取作业列表失败')
          const d = response.data || {}
          items = d.items || []
          page = d.page || 1
          size = d.size || this.pagination.pageSize
          total = d.total || 0
          pages = d.pages || 0
        } else {
          // 旧结构：直接返回分页对象
          items = response?.items || []
          page = response?.page || 1
          size = response?.size || this.pagination.pageSize
          total = response?.total || 0
          pages = response?.pages || 0
        }
        this.homeworks = items
        this.pagination = {
          current: page,
          pageSize: size,
          total,
          pages
        }
        return response
      } catch (error) {
        console.error('获取作业失败:', error)
        message.error('获取作业列表失败')
        // 失败时清空数据并不中断后续流程
        this.homeworks = []
        return { success: false, message: error?.message || '获取作业列表失败' }
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取作业详情
     */
    async fetchHomework(id) {
      this.loading = true
      try {
        const response = await homeworkApi.getHomework(id)
        if (response.success) {
          this.currentHomework = response.data
          return response.data
        } else {
          throw new Error(response.message || '获取作业详情失败')
        }
      } catch (error) {
        console.error('获取作业详情失败:', error)
        message.error('获取作业详情失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 创建作业
     */
    async createHomework(data) {
      this.loading = true
      try {
        const response = await homeworkApi.createHomework(data)
        if (response.success) {
          message.success('作业创建成功')
          return response.data
        } else {
          throw new Error(response.message || '创建作业失败')
        }
      } catch (error) {
        console.error('创建作业失败:', error)
        message.error('创建作业失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 更新作业
     */
    async updateHomework(id, data) {
      this.loading = true
      try {
        const response = await homeworkApi.updateHomework(id, data)
        if (response.success) {
          message.success('作业更新成功')
          // 更新本地数据
          const index = this.homeworks.findIndex(h => h.id === id)
          if (index !== -1) {
            this.homeworks[index] = { ...this.homeworks[index], ...data }
          }
          if (this.currentHomework && this.currentHomework.id === id) {
            this.currentHomework = { ...this.currentHomework, ...data }
          }
          return response.data
        } else {
          throw new Error(response.message || '更新作业失败')
        }
      } catch (error) {
        console.error('更新作业失败:', error)
        message.error('更新作业失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 删除作业
     */
    async deleteHomework(id) {
      this.loading = true
      try {
        const response = await homeworkApi.deleteHomework(id)
        if (response.success) {
          message.success('作业删除成功')
          // 从本地数据中移除
          this.homeworks = this.homeworks.filter(h => h.id !== id)
          if (this.currentHomework && this.currentHomework.id === id) {
            this.currentHomework = null
          }
          return response
        } else {
          throw new Error(response.message || '删除作业失败')
        }
      } catch (error) {
        console.error('删除作业失败:', error)
        message.error('删除作业失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取作业进度
     */
    async fetchHomeworkProgress(id) {
      try {
        const response = await homeworkApi.getHomeworkProgress(id)
        if (response.success) {
          return response.data
        } else {
          throw new Error(response.message || '获取作业进度失败')
        }
      } catch (error) {
        console.error('获取作业进度失败:', error)
        message.error('获取作业进度失败')
        throw error
      }
    },

    /**
     * 发布作业
     */
    async publishHomework(id) {
      try {
        const response = await homeworkApi.publishHomework(id)
        if (response.success) {
          message.success('作业发布成功')
          // 更新本地作业状态
          const index = this.homeworks.findIndex(h => h.id === id)
          if (index !== -1) {
            this.homeworks[index].status = 'published'
          }
          return response.data
        } else {
          throw new Error(response.message || '发布作业失败')
        }
      } catch (error) {
        console.error('发布作业失败:', error)
        message.error('发布作业失败')
        throw error
      }
    },

    /**
     * 设置当前作业
     */
    setCurrentHomework(homework) {
      this.currentHomework = homework
    },

    /**
     * 获取学生作业列表
     */
    async fetchStudentHomeworks(params = {}) {
      this.loading = true
      try {
        const response = await homeworkApi.getStudentHomeworks(params)
        // 兼容 BaseResponse 与直接分页响应两种结构
        let items, page, size, total, pages, success = true
        if (response && Object.prototype.hasOwnProperty.call(response, 'success')) {
          success = !!response.success
          if (!success) throw new Error(response.message || '获取学生作业列表失败')
          const d = response.data || {}
          items = d.items || []
          page = d.page || 1
          size = d.size || this.studentPagination.pageSize
          total = d.total || 0
          pages = d.pages || 0
        } else {
          items = response?.items || []
          page = response?.page || 1
          size = response?.size || this.studentPagination.pageSize
          total = response?.total || 0
          pages = response?.pages || 0
        }
        this.studentHomeworks = items
        this.studentPagination = {
          current: page,
          pageSize: size,
          total,
          pages
        }
        return response
      } catch (error) {
        console.error('获取学生作业失败:', error)
        message.error('获取学生作业列表失败')
        this.studentHomeworks = []
        return { success: false, message: error?.message || '获取学生作业列表失败' }
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取学生作业详情
     */
    async fetchStudentHomework(id) {
      this.loading = true
      try {
        const response = await homeworkApi.getStudentHomework(id)
        if (response.success) {
          this.currentStudentHomework = response.data
          return response.data
        } else {
          throw new Error(response.message || '获取学生作业详情失败')
        }
      } catch (error) {
        console.error('获取学生作业详情失败:', error)
        message.error('获取学生作业详情失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 开始作业
     */
    async startHomework(id) {
      try {
        const response = await homeworkApi.startHomework(id)
        if (response.success) {
          message.success('作业已开始')
          // 更新作业状态
          const index = this.studentHomeworks.findIndex(h => h.id === id)
          if (index !== -1) {
            this.studentHomeworks[index].status = 'in_progress'
          }
          return response.data
        } else {
          throw new Error(response.message || '开始作业失败')
        }
      } catch (error) {
        console.error('开始作业失败:', error)
        message.error('开始作业失败')
        throw error
      }
    },

    /**
     * 提交作业答案
     */
    async submitAnswer(homeworkId, questionId, answer) {
      try {
        const response = await homeworkApi.submitAnswer(homeworkId, questionId, answer)
        if (response.success) {
          return response.data
        } else {
          throw new Error(response.message || '提交答案失败')
        }
      } catch (error) {
        console.error('提交答案失败:', error)
        message.error('提交答案失败')
        throw error
      }
    },

    /**
     * 完成作业
     */
    async completeHomework(id) {
      try {
        const response = await homeworkApi.completeHomework(id)
        if (response.success) {
          message.success('作业已完成')
          // 更新作业状态
          const index = this.studentHomeworks.findIndex(h => h.id === id)
          if (index !== -1) {
            this.studentHomeworks[index].status = 'completed'
          }
          return response.data
        } else {
          throw new Error(response.message || '完成作业失败')
        }
      } catch (error) {
        console.error('完成作业失败:', error)
        message.error('完成作业失败')
        throw error
      }
    },

    /**
     * 获取我的作业进度
     */
    async fetchMyProgress(homeworkId) {
      try {
        const response = await homeworkApi.getMyProgress(homeworkId)
        if (response.success) {
          return response.data
        } else {
          throw new Error(response.message || '获取作业进度失败')
        }
      } catch (error) {
        console.error('获取作业进度失败:', error)
        message.error('获取作业进度失败')
        throw error
      }
    },

    /**
     * 设置当前学生作业
     */
    setCurrentStudentHomework(homework) {
      this.currentStudentHomework = homework
    },

    /**
     * 清空作业列表
     */
    clearHomeworks() {
      this.homeworks = []
      this.currentHomework = null
      this.pagination = {
        current: 1,
        pageSize: 10,
        total: 0,
        pages: 0
      }
    },

    /**
     * 清空学生作业列表
     */
    clearStudentHomeworks() {
      this.studentHomeworks = []
      this.currentStudentHomework = null
      this.studentPagination = {
        current: 1,
        pageSize: 10,
        total: 0,
        pages: 0
      }
    }
  }
})
