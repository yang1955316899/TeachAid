import http from '@/utils/http'

/**
 * 授课关系管理API
 */
export const teachingApi = {
  /**
   * 获取我的授课关系
   */
  getMyTeaching(params = {}) {
    return http.get('/teaching/my', { params })
  },

  /**
   * 获取所有授课关系（管理员）
   */
  getAllTeaching(params = {}) {
    return http.get('/teaching/all', { params })
  },

  /**
   * 创建授课关系
   */
  createTeaching(data) {
    const payload = { ...data }
    if (payload.classId && !payload.class_id) payload.class_id = payload.classId
    if (payload.subjectId && !payload.subject_id) payload.subject_id = payload.subjectId
    return http.post('/teaching', payload)
  },

  /**
   * 更新授课关系
   */
  updateTeaching(id, data) {
    return http.put(`/teaching/${id}`, data)
  },

  /**
   * 删除授课关系
   */
  deleteTeaching(id) {
    return http.delete(`/teaching/${id}`)
  },

  /**
   * 按学科获取授课班级
   */
  getClassesBySubject(subjectId = null) {
    const params = {}
    if (subjectId) params.subject_id = subjectId
    return http.get('/teaching/classes-by-subject', { params })
  },

  /**
   * 按班级获取授课学科
   */
  getSubjectsByClass(classId = null) {
    const params = {}
    if (classId) params.class_id = classId
    return http.get('/teaching/subjects-by-class', { params })
  }
}