import { defineStore } from 'pinia'
import { homeworkApi } from '@/api/homework'
import { message } from 'ant-design-vue'

export const useStudentHomeworkStore = defineStore('studentHomework', {
  state: () => ({
    homeworks: [],
    currentHomework: null,
    loading: false,
    pagination: {
      current: 1,
      pageSize: 10,
      total: 0,
      pages: 0
    }
  }),
  
  getters: {
    homeworkCount: (state) => state.homeworks.length,
    completedHomeworks: (state) => state.homeworks.filter(h => h.status === 'completed'),
    pendingHomeworks: (state) => state.homeworks.filter(h => h.status === 'pending'),
    overdueHomeworks: (state) => state.homeworks.filter(h => h.status === 'overdue')
  },
  
  actions: {
    /**
     * 获取学生作业列表
     */
    async fetchStudentHomeworks(params = {}) {
      this.loading = true
      try {
        const response = await homeworkApi.getStudentHomeworks(params)
        if (response.success) {
          this.homeworks = response.data.items
          this.pagination = {
            current: response.data.page,
            pageSize: response.data.size,
            total: response.data.total,
            pages: response.data.pages
          }
          return response
        } else {
          throw new Error(response.message || '获取作业列表失败')
        }
      } catch (error) {
        console.error('获取作业失败:', error)
        message.error('获取作业列表失败')
        throw error
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
        const response = await homeworkApi.getStudentHomework(id)
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
     * 开始作业
     */
    async startHomework(id) {
      try {
        const response = await homeworkApi.startHomework(id)
        if (response.success) {
          message.success('作业已开始')
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
          // 更新本地作业状态
          const index = this.homeworks.findIndex(h => h.id === id)
          if (index !== -1) {
            this.homeworks[index].status = 'completed'
            this.homeworks[index].completed_at = new Date().toISOString()
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
     * 获取作业结果
     */
    async getHomeworkResult(id) {
      try {
        const response = await homeworkApi.getHomeworkResult(id)
        if (response.success) {
          return response.data
        } else {
          throw new Error(response.message || '获取作业结果失败')
        }
      } catch (error) {
        console.error('获取作业结果失败:', error)
        message.error('获取作业结果失败')
        throw error
      }
    },

    /**
     * 获取学习进度
     */
    async getStudentProgress(homeworkId) {
      try {
        const response = await homeworkApi.getStudentProgress(homeworkId)
        if (response.success) {
          return response.data
        } else {
          throw new Error(response.message || '获取学习进度失败')
        }
      } catch (error) {
        console.error('获取学习进度失败:', error)
        message.error('获取学习进度失败')
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
    }
  }
})