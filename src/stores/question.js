import { defineStore } from 'pinia'

export const useQuestionStore = defineStore('question', {
  state: () => ({
    questions: [],
    currentQuestion: null,
    loading: false,
    uploadProgress: 0
  }),
  
  getters: {
    questionCount: (state) => state.questions.length,
    questionsBySubject: (state) => {
      return (subject) => state.questions.filter(q => q.subject === subject)
    }
  },
  
  actions: {
    async fetchQuestions(params = {}) {
      this.loading = true
      try {
        // 模拟API调用
        const response = await this.mockFetchQuestions(params)
        this.questions = response.data
        return response
      } catch (error) {
        console.error('获取题目失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async uploadQuestion(file) {
      try {
        this.uploadProgress = 0
        // 模拟上传进度
        const progressInterval = setInterval(() => {
          this.uploadProgress += 10
          if (this.uploadProgress >= 100) {
            clearInterval(progressInterval)
          }
        }, 200)
        
        const response = await this.mockUploadQuestion(file)
        return response
      } catch (error) {
        console.error('上传题目失败:', error)
        throw error
      }
    },
    
    async rewriteAnswer(questionId, config) {
      try {
        const response = await this.mockRewriteAnswer(questionId, config)
        // 更新本地题目数据
        const index = this.questions.findIndex(q => q.id === questionId)
        if (index !== -1) {
          this.questions[index] = { ...this.questions[index], ...response.data }
        }
        return response
      } catch (error) {
        console.error('改写答案失败:', error)
        throw error
      }
    },
    
    setCurrentQuestion(question) {
      this.currentQuestion = question
    },
    
    // 模拟API方法
    async mockFetchQuestions(params) {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            data: [
              {
                id: '1',
                title: '二次函数综合应用题',
                subject: '数学',
                type: '解答题',
                content: '已知二次函数f(x) = ax² + bx + c...',
                originalAnswer: '原始解答步骤...',
                rewrittenAnswer: 'AI改写后的引导式解答...',
                createTime: '2024-01-15',
                status: '已改写'
              },
              {
                id: '2',
                title: '英语完形填空',
                subject: '英语',
                type: '选择题',
                content: 'The following passage...',
                originalAnswer: 'A B C D',
                rewrittenAnswer: '让我们一起分析每个选项...',
                createTime: '2024-01-14',
                status: '待改写'
              }
            ],
            total: 20
          })
        }, 500)
      })
    },
    
    async mockUploadQuestion(file) {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: true,
            data: {
              id: Date.now().toString(),
              filename: file.name,
              status: 'processing'
            }
          })
        }, 2000)
      })
    },
    
    async mockRewriteAnswer(questionId, config) {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: true,
            data: {
              rewrittenAnswer: '这是AI改写后的引导式答案...',
              status: '已改写'
            }
          })
        }, 1500)
      })
    }
  }
})