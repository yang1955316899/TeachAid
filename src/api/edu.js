import http from '@/utils/http'

export const eduApi = {
  getGrades() {
    return http.get('/taxonomy/grades')
  },
  getSubjects() {
    return http.get('/taxonomy/subjects')
  },
  getChapters(params = {}) {
    return http.get('/taxonomy/chapters', { params })
  }
}

