import http from '@/utils/http'

/**
 * 提示词模板管理API
 */
export const promptApi = {
  /**
   * 获取提示词模板列表
   */
  getPrompts(params = {}) {
    return http.get('/prompts', { params })
  },

  /**
   * 获取提示词模板详情
   */
  getPrompt(templateId) {
    return http.get(`/prompts/${templateId}`)
  },

  /**
   * 创建提示词模板
   */
  createPrompt(data) {
    return http.post('/prompts', data)
  },

  /**
   * 更新提示词模板
   */
  updatePrompt(templateId, data) {
    return http.put(`/prompts/${templateId}`, data)
  },

  /**
   * 删除提示词模板
   */
  deletePrompt(templateId) {
    return http.delete(`/prompts/${templateId}`)
  },

  /**
   * 获取公开提示词模板
   */
  getPublicPrompts(params = {}) {
    return http.get('/prompts/public/templates', { params })
  }
}