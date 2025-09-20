/**
 * 管理员API接口
 */
import http from '@/utils/http'

const adminApi = {
  // ============ 系统统计 ============
  getSystemStats() {
    return http.get('/admin/stats')
  },

  // ============ 用户管理 ============
  getUsers(params) {
    return http.get('/admin/users', { params })
  },

  createUser(data) {
    return http.post('/admin/users', data)
  },

  updateUser(userId, data) {
    return http.put(`/admin/users/${userId}`, data)
  },

  deleteUser(userId) {
    return http.delete(`/admin/users/${userId}`)
  },

  resetUserPassword(userId, data) {
    return http.post(`/admin/users/${userId}/reset-password`, data)
  },

  getUserLoginLogs(userId, params) {
    return http.get(`/admin/users/${userId}/login-logs`, { params })
  },

  // ============ 班级管理 ============
  getClasses(params) {
    return http.get('/admin/classes', { params })
  },

  createClass(data) {
    return http.post('/admin/classes', data)
  },

  updateClass(classId, data) {
    return http.put(`/admin/classes/${classId}`, data)
  },

  deleteClass(classId) {
    return http.delete(`/admin/classes/${classId}`)
  },

  getClassStudents(classId, params) {
    return http.get(`/admin/classes/${classId}/students`, { params })
  },

  addStudentToClass(classId, studentId) {
    return http.post(`/admin/classes/${classId}/students/${studentId}`)
  },

  removeStudentFromClass(classId, studentId) {
    return http.delete(`/admin/classes/${classId}/students/${studentId}`)
  },

  createTeachingAssignment(data) {
    return http.post('/admin/teaching-assignments', data)
  },

  // ============ 作业管理 ============
  getHomeworks(params) {
    return http.get('/admin/homeworks', { params })
  },

  getHomeworkStudents(homeworkId, params) {
    return http.get(`/admin/homeworks/${homeworkId}/students`, { params })
  },

  publishHomework(homeworkId) {
    return http.post(`/admin/homeworks/${homeworkId}/publish`)
  },

  unpublishHomework(homeworkId) {
    return http.post(`/admin/homeworks/${homeworkId}/unpublish`)
  },

  // ============ 题目管理 ============
  getQuestions(params) {
    return http.get('/admin/questions', { params })
  },

  getQuestionDetail(questionId) {
    return http.get(`/admin/questions/${questionId}`)
  },

  updateQuestionStatus(questionId, isActive) {
    return http.put(`/admin/questions/${questionId}/status`, null, {
      params: { is_active: isActive }
    })
  },

  updateQuestionPublicity(questionId, isPublic) {
    return http.put(`/admin/questions/${questionId}/publicity`, null, {
      params: { is_public: isPublic }
    })
  },

  deleteQuestion(questionId) {
    return http.delete(`/admin/questions/${questionId}`)
  },

  // ============ 系统配置 ============
  getSystemSettings(params) {
    return http.get('/admin/system-settings', { params })
  },

  getSettingCategories() {
    return http.get('/admin/system-settings/categories')
  },

  createSystemSetting(data) {
    return http.post('/admin/system-settings', data)
  },

  updateSystemSetting(systemId, data) {
    return http.put(`/admin/system-settings/${systemId}`, data)
  },

  deleteSystemSetting(systemId) {
    return http.delete(`/admin/system-settings/${systemId}`)
  },

  // ============ 权限管理 ============
  getPermissions(params) {
    return http.get('/admin/permissions', { params })
  },

  createPermission(data) {
    return http.post('/admin/permissions', data)
  },

  getRolePermissions(role) {
    return http.get(`/admin/roles/${role}/permissions`)
  },

  assignPermissionToRole(role, permissionId, isGranted) {
    return http.post(`/admin/roles/${role}/permissions/${permissionId}`, null, {
      params: { is_granted: isGranted }
    })
  },

  // ============ 数据分析 ============
  getAnalyticsOverview(params) {
    return http.get('/admin/analytics/overview', { params })
  },

  getUserAnalytics(params) {
    return http.get('/admin/analytics/users', { params })
  },

  getContentAnalytics(params) {
    return http.get('/admin/analytics/content', { params })
  },

  exportAnalyticsData(params) {
    return http.get('/admin/analytics/export', {
      params,
      responseType: 'blob'
    })
  }
}

export default adminApi