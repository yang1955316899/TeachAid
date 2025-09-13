import { defineStore } from 'pinia'
import { chatApi } from '@/api/chat'
import { message } from 'ant-design-vue'

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
    async startChatSession(questionId) {
      this.loading = true
      try {
        const response = await chatApi.startSession({
          question_id: questionId
        })
        
        if (response.success) {
          this.currentSession = response.data
          this.messages = []
          return response
        } else {
          throw new Error(response.message || '创建对话会话失败')
        }
      } catch (error) {
        console.error('创建对话会话失败:', error)
        message.error('创建对话会话失败')
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async sendMessage(content, selectedText = null) {
      if (!this.currentSession) {
        throw new Error('没有活跃的对话会话')
      }
      
      // 添加用户消息到本地状态
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content,
        selected_text: selectedText,
        created_at: new Date().toISOString()
      }
      this.messages.push(userMessage)
      
      this.loading = true
      try {
        // 调用后端API
        const response = await chatApi.sendMessage(this.currentSession.id, {
          content,
          selected_text: selectedText
        })
        
        if (response.success) {
          // 添加AI回复到本地状态
          const aiMessage = {
            id: Date.now() + 1,
            role: 'assistant',
            content: response.data.content,
            created_at: new Date().toISOString()
          }
          this.messages.push(aiMessage)
          return response
        } else {
          throw new Error(response.message || '发送消息失败')
        }
      } catch (error) {
        console.error('发送消息失败:', error)
        message.error('发送消息失败')
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async getChatHistory(sessionId) {
      this.loading = true
      try {
        const response = await chatApi.getChatHistory(sessionId)
        
        if (response.success) {
          this.messages = response.data.messages || []
          return response
        } else {
          throw new Error(response.message || '获取对话历史失败')
        }
      } catch (error) {
        console.error('获取对话历史失败:', error)
        message.error('获取对话历史失败')
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async streamChat(sessionId, content, selectedText = null) {
      if (!this.currentSession) {
        throw new Error('没有活跃的对话会话')
      }
      
      // 添加用户消息到本地状态
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content,
        selected_text: selectedText,
        created_at: new Date().toISOString()
      }
      this.messages.push(userMessage)
      
      try {
        // 调用流式API
        const response = await chatApi.streamChat(sessionId, {
          content,
          selected_text: selectedText
        })
        
        // 处理流式响应
        return response
      } catch (error) {
        console.error('流式对话失败:', error)
        message.error('对话失败')
        throw error
      }
    },
    
    clearCurrentSession() {
      this.currentSession = null
      this.messages = []
    }
  }
})