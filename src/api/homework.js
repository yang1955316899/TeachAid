import http from '@/utils/http'

/**
 * 作业管理API
 */
export const homeworkApi = {
  /**
   * 获取作业列表
   */
  getHomeworks(params = {}) {
    return http.get('/homework', { params })
  },

  /**
   * 获取作业详情
   */
  getHomework(id) {
    return http.get(`/homework/${id}`)
  },

  /**
   * 创建作业
   */
  createHomework(data) {
    const payload = { ...data }
    if (payload.subjectId && !payload.subject_id) payload.subject_id = payload.subjectId
    if (payload.classId && !payload.class_id) payload.class_id = payload.classId
    return http.post('/homework', payload)
  },

  /**
   * 更新作业
   */
  updateHomework(id, data) {
    return http.put(`/homework/${id}`, data)
  },

  /**
   * 删除作业
   */
  deleteHomework(id) {
    return http.delete(`/homework/${id}`)
  },

  /**
   * 获取作业进度
   */
  getHomeworkProgress(id) {
    return http.get(`/homework/${id}/progress`)
  },

  /**
   * 发布作业
   */
  publishHomework(id) {
    return http.post(`/homework/${id}/publish`)
  },

  /**
   * 提交作业
   */
  submitHomework(id, data) {
    return http.post(`/homework/${id}/submit`, data)
  },

  /**
   * 获取学生作业进度
   */
  getStudentProgress(studentId, homeworkId) {
    return http.get(`/homework/${homeworkId}/student/${studentId}/progress`)
  },

  /**
   * 获取学生作业列表
   */
  getStudentHomeworks(params = {}) {
    return http.get('/student/homework', { params })
  },

  /**
   * 获取学生作业详情
   */
  getStudentHomework(id) {
    return http.get(`/student/homework/${id}`)
  },

  /**
   * 开始作业
   */
  startHomework(id) {
    return http.post(`/student/homework/${id}/start`)
  },

  /**
   * 提交答案
   */
  submitAnswer(homeworkId, questionId, answer) {
    return http.post(`/student/homework/${homeworkId}/questions/${questionId}/answer`, { answer })
  },

  /**
   * 完成作业
   */
  completeHomework(id) {
    return http.post(`/student/homework/${id}/complete`)
  },

  /**
   * 获取作业结果
   */
  getHomeworkResult(id) {
    return http.get(`/student/homework/${id}/result`)
  },

  /**
   * 获取当前学生的学习进度
   */
  getMyProgress(homeworkId) {
    return http.get(`/student/homework/${homeworkId}/my-progress`)
  }
}
