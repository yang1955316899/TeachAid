import http from '@/utils/http'

/**
 * 班级管理API
 */
export const classApi = {
  /**
   * 获取班级列表
   */
  getClasses(params = {}) {
    return http.get('/classes', { params })
  },

  /**
   * 获取班级详情
   */
  getClass(id) {
    return http.get(`/classes/${id}`)
  },

  /**
   * 创建班级
   */
  createClass(data) {
    return http.post('/classes', data)
  },

  /**
   * 更新班级
   */
  updateClass(id, data) {
    return http.put(`/classes/${id}`, data)
  },

  /**
   * 删除班级
   */
  deleteClass(id) {
    return http.delete(`/classes/${id}`)
  },

  /**
   * 获取班级学生列表
   */
  getClassStudents(classId) {
    return http.get(`/classes/${classId}/students`)
  },

  /**
   * 添加学生到班级
   */
  addStudentToClass(classId, studentId) {
    return http.post(`/classes/${classId}/students`, { student_id: studentId })
  },

  /**
   * 从班级移除学生
   */
  removeStudentFromClass(classId, studentId) {
    return http.delete(`/classes/${classId}/students/${studentId}`)
  }
}