import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', {
  state: () => ({
    currentSession: null,
    messages: [],
    loading: false,
    sessions: []
  }),
  
  getters: {
    messageCount: (state) => state.messages.length,
    lastMessage: (state) => state.messages[state.messages.length - 1] || null
  },
  
  actions: {
    async startChatSession(questionId, studentId) {
      try {
        const response = await this.mockStartSession(questionId, studentId)
        this.currentSession = response.session
        this.messages = []
        return response
      } catch (error) {
        console.error('创建对话会话失败:', error)
        throw error
      }
    },
    
    async sendMessage(content, selectedText = null) {
      if (!this.currentSession) {
        throw new Error('没有活跃的对话会话')
      }
      
      // 添加用户消息
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content,
        selectedText,
        timestamp: new Date().toISOString()
      }
      this.messages.push(userMessage)
      
      this.loading = true
      try {
        // 调用AI API
        const response = await this.mockSendMessage(content, selectedText)
        
        // 添加AI回复
        const aiMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.reply,
          timestamp: new Date().toISOString()
        }
        this.messages.push(aiMessage)
        
        return response
      } catch (error) {
        console.error('发送消息失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async getChatHistory(sessionId) {
      try {
        const response = await this.mockGetHistory(sessionId)
        this.messages = response.messages
        return response
      } catch (error) {
        console.error('获取对话历史失败:', error)
        throw error
      }
    },
    
    clearCurrentSession() {
      this.currentSession = null
      this.messages = []
    },
    
    // 模拟API方法
    async mockStartSession(questionId, studentId) {
      return new Promise((resolve) => {
        setTimeout(() => {
          const session = {
            id: `session_${Date.now()}`,
            questionId,
            studentId,
            startTime: new Date().toISOString(),
            status: 'active'
          }
          resolve({
            success: true,
            session
          })
        }, 500)
      })
    },
    
    async mockSendMessage(content, selectedText) {
      return new Promise((resolve) => {
        setTimeout(() => {
          let reply = '这是一个很好的问题！'
          
          if (selectedText) {
            reply = `关于你选中的内容"${selectedText}"，让我来解释一下...`
          } else if (content.includes('不懂') || content.includes('不会')) {
            reply = '没关系，让我们一步步来分析这个问题。首先...'
          } else if (content.includes('为什么')) {
            reply = '这个问题问得很好！原因是...'
          }
          
          resolve({
            success: true,
            reply,
            sessionId: this.currentSession?.id
          })
        }, 1000 + Math.random() * 1000) // 模拟1-2秒的响应时间
      })
    },
    
    async mockGetHistory(sessionId) {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: true,
            messages: [
              {
                id: 1,
                role: 'assistant',
                content: '你好！我是你的AI学习助手，有什么问题可以随时问我。',
                timestamp: new Date(Date.now() - 10000).toISOString()
              }
            ]
          })
        }, 300)
      })
    }
  }
})