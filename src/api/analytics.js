import http from '@/utils/http'

export const analyticsApi = {
  // 班级学习概览（教师）
  getClassOverview(classId, params = {}) {
    return http.get(`/analytics/class/${classId}/overview`, { params })
  },

  // 学生学习报告（教师或本人）
  getStudentReport(studentId, params = {}) {
    return http.get(`/analytics/student/${studentId}/report`, { params })
  }
}

