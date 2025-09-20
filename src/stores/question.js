import { defineStore } from 'pinia'
import { questionApi } from '@/api/question'
import { message } from 'ant-design-vue'

export const useQuestionStore = defineStore('question', {
  state: () => ({
    questions: [],
    currentQuestion: null,
    loading: false,
    uploadProgress: 0,
    pagination: {
      current: 1,
      pageSize: 10,
      total: 0,
      pages: 0
    }
  }),
  
  getters: {
    questionCount: (state) => state.questions.length,
    questionsBySubject: (state) => {
      return (subject) => state.questions.filter(q => q.subject === subject)
    }
  },
  
  actions: {
    /**
     * 获取题目列表
     */
    async fetchQuestions(params = {}) {
      this.loading = true
      try {
        const response = await questionApi.getQuestions(params)
        // 兼容 BaseResponse 与直接分页响应两种结构
        let items, page, size, total, pages, success = true
        if (response && Object.prototype.hasOwnProperty.call(response, 'success')) {
          success = !!response.success
          const d = success ? (response.data || {}) : {}
          items = d.items || []
          page = d.page || 1
          size = d.size || this.pagination.pageSize
          total = d.total || 0
          pages = d.pages || 0
        } else {
          items = response?.items || []
          page = response?.page || 1
          size = response?.size || this.pagination.pageSize
          total = response?.total || 0
          pages = response?.pages || 0
        }
        this.questions = items
        this.pagination = {
          current: page,
          pageSize: size,
          total,
          pages
        }
        return response
      } catch (error) {
        console.error('获取题目失败:', error)
        message.error('获取题目列表失败')
        // 失败时清空数据并不中断后续流程
        this.questions = []
        // 不再向上抛错，避免页面 mounted 流程中断
        return { success: false, message: error?.message || '获取题目列表失败' }
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取题目详情
     */
    async fetchQuestion(id) {
      this.loading = true
      try {
        const response = await questionApi.getQuestion(id)
        if (response.success) {
          this.currentQuestion = response.data
          return response.data
        } else {
          throw new Error(response.message || '获取题目详情失败')
        }
      } catch (error) {
        console.error('获取题目详情失败:', error)
        message.error('获取题目详情失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 创建题目
     */
    async createQuestion(data) {
      this.loading = true
      try {
        const response = await questionApi.createQuestion(data)
        if (response.success) {
          message.success('题目创建成功')
          return response.data
        } else {
          throw new Error(response.message || '创建题目失败')
        }
      } catch (error) {
        console.error('创建题目失败:', error)
        message.error('创建题目失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 更新题目
     */
    async updateQuestion(id, data) {
      this.loading = true
      try {
        const response = await questionApi.updateQuestion(id, data)
        if (response.success) {
          message.success('题目更新成功')
          // 更新本地数据
          const index = this.questions.findIndex(q => q.id === id)
          if (index !== -1) {
            this.questions[index] = { ...this.questions[index], ...data }
          }
          if (this.currentQuestion && this.currentQuestion.id === id) {
            this.currentQuestion = { ...this.currentQuestion, ...data }
          }
          return response.data
        } else {
          throw new Error(response.message || '更新题目失败')
        }
      } catch (error) {
        console.error('更新题目失败:', error)
        message.error('更新题目失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 删除题目
     */
    async deleteQuestion(id) {
      this.loading = true
      try {
        const response = await questionApi.deleteQuestion(id)
        if (response.success) {
          message.success('题目删除成功')
          // 从本地数据中移除
          this.questions = this.questions.filter(q => q.id !== id)
          if (this.currentQuestion && this.currentQuestion.id === id) {
            this.currentQuestion = null
          }
          return response
        } else {
          throw new Error(response.message || '删除题目失败')
        }
      } catch (error) {
        console.error('删除题目失败:', error)
        message.error('删除题目失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 上传题目文件
     */
    async uploadQuestion(file) {
      try {
        this.uploadProgress = 0
        const response = await questionApi.uploadQuestionFile(file)
        if (response.success) {
          message.success('文件上传成功')
          return response.data
        } else {
          throw new Error(response.message || '文件上传失败')
        }
      } catch (error) {
        console.error('上传题目失败:', error)
        message.error('文件上传失败')
        throw error
      }
    },

    /**
     * 改写答案
     */
    async rewriteAnswer(questionId, config) {
      this.loading = true
      try {
        const response = await questionApi.rewriteAnswer(questionId, config)
        if (response.success) {
          message.success('答案改写成功')
          // 更新本地题目数据
          const index = this.questions.findIndex(q => q.id === questionId)
          if (index !== -1) {
            this.questions[index] = { 
              ...this.questions[index], 
              rewritten_answer: response.data.rewritten_answer,
              quality_score: response.data.quality_score
            }
          }
          if (this.currentQuestion && this.currentQuestion.id === questionId) {
            this.currentQuestion = {
              ...this.currentQuestion,
              rewritten_answer: response.data.rewritten_answer,
              quality_score: response.data.quality_score
            }
          }
          return response.data
        } else {
          throw new Error(response.message || '改写答案失败')
        }
      } catch (error) {
        console.error('改写答案失败:', error)
        message.error('改写答案失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 设置当前题目
     */
    setCurrentQuestion(question) {
      this.currentQuestion = question
    },

    /**
     * 清空题目列表
     */
    clearQuestions() {
      this.questions = []
      this.currentQuestion = null
      this.pagination = {
        current: 1,
        pageSize: 10,
        total: 0,
        pages: 0
      }
    }
  }
})
