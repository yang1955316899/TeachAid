import http from '@/utils/http'

/**
 * 教务维度API - 年级、学科、章节
 */
export const taxonomyApi = {
  /**
   * 获取年级列表
   */
  getGrades() {
    return http.get('/taxonomy/grades')
  },

  /**
   * 获取学科列表
   */
  getSubjects() {
    return http.get('/taxonomy/subjects')
  },

  /**
   * 获取章节列表
   */
  getChapters(params = {}) {
    return http.get('/taxonomy/chapters', { params })
  }
}