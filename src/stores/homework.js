import { defineStore } from 'pinia'
import { homeworkApi } from '@/api/homework'
import { message } from 'ant-design-vue'

export const useHomeworkStore = defineStore('homework', {
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
    homeworkByClass: (state) => {
      return (className) => state.homeworks.filter(h => h.class_name === className)
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