import http from '@/utils/http'

/**
 * 题目管理API
 */
export const questionApi = {
  /**
   * 获取题目列表
   */
  getQuestions(params = {}) {
    return http.get('/questions/public', { params })
  },

  /**
   * 获取题目详情
   */
  getQuestion(id) {
    return http.get(`/questions/${id}`)
  },

  /**
   * 创建题目
   */
  createQuestion(data) {
    return http.post('/questions', data)
  },

  /**
   * 更新题目
   */
  updateQuestion(id, data) {
    return http.put(`/questions/${id}`, data)
  },

  /**
   * 删除题目
   */
  deleteQuestion(id) {
    return http.delete(`/questions/${id}`)
  },

  /**
   * 上传题目文件
   */
  uploadQuestionFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    return http.post('/questions/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 获取文件处理状态
   */
  getUploadStatus(fileId) {
    return http.get(`/questions/upload/${fileId}/status`)
  },

  /**
   * 改写答案
   */
  rewriteAnswer(questionId, data) {
    return http.put(`/questions/${questionId}/rewrite`, data)
  }
}