import http from '@/utils/http'

/**
 * 聊天相关API
 */
export const chatApi = {
  /**
   * 开始对话会话
   */
  startSession(data) {
    return http.post('/chat/sessions', data)
  },

  /**
   * 发送消息
   */
  sendMessage(sessionId, data) {
    return http.post(`/chat/${sessionId}/messages`, data)
  },

  /**
   * 获取对话历史
   */
  getChatHistory(sessionId) {
    return http.get(`/chat/${sessionId}/messages`)
  },

  /**
   * 流式对话
   */
  streamChat(sessionId, data) {
    return http.post(`/chat/${sessionId}/stream`, data, {
      responseType: 'stream'
    })
  },

  /**
   * 结束对话
   */
  endSession(sessionId) {
    return http.post(`/chat/${sessionId}/end`)
  }
}