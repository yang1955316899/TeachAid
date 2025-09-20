import { defineStore } from 'pinia'
import { taxonomyApi } from '@/api/taxonomy'
import { message } from 'ant-design-vue'

export const useTaxonomyStore = defineStore('taxonomy', {
  state: () => ({
    grades: [],
    subjects: [],
    chapters: [],
    loading: false
  }),

  getters: {
    subjectOptions: (state) => {
      return state.subjects.map(subject => ({
        label: subject.name,
        value: subject.id
      }))
    },

    gradeOptions: (state) => {
      return state.grades.map(grade => ({
        label: grade.name,
        value: grade.id
      }))
    }
  },

  actions: {
    /**
     * 获取年级列表
     */
    async fetchGrades() {
      this.loading = true
      try {
        const response = await taxonomyApi.getGrades()
        if (response.success) {
          this.grades = response.data.items || []
        } else {
          throw new Error(response.message || '获取年级列表失败')
        }
        return response
      } catch (error) {
        console.error('获取年级列表失败:', error)
        message.error('获取年级列表失败')
        return { success: false, message: error?.message || '获取年级列表失败' }
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取学科列表
     */
    async fetchSubjects() {
      this.loading = true
      try {
        const response = await taxonomyApi.getSubjects()
        if (response.success) {
          this.subjects = response.data.items || []
        } else {
          throw new Error(response.message || '获取学科列表失败')
        }
        return response
      } catch (error) {
        console.error('获取学科列表失败:', error)
        message.error('获取学科列表失败')
        return { success: false, message: error?.message || '获取学科列表失败' }
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取章节列表
     */
    async fetchChapters(params = {}) {
      this.loading = true
      try {
        const response = await taxonomyApi.getChapters(params)
        if (response.success) {
          this.chapters = response.data.items || []
        } else {
          throw new Error(response.message || '获取章节列表失败')
        }
        return response
      } catch (error) {
        console.error('获取章节列表失败:', error)
        message.error('获取章节列表失败')
        return { success: false, message: error?.message || '获取章节列表失败' }
      } finally {
        this.loading = false
      }
    },

    /**
     * 清空数据
     */
    clearData() {
      this.grades = []
      this.subjects = []
      this.chapters = []
    }
  }
})