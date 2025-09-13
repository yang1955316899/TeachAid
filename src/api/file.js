import http from '@/utils/http'

/**
 * 文件管理API
 */
export const fileApi = {
  /**
   * 获取文件列表
   */
  getFiles(params = {}) {
    return http.get('/files', { params })
  },

  /**
   * 获取文件详情
   */
  getFile(fileId) {
    return http.get(`/files/${fileId}`)
  },

  /**
   * 上传文件
   */
  uploadFile(file, isPublic = false) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('is_public', isPublic)
    return http.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 下载文件
   */
  downloadFile(fileId) {
    return http.get(`/files/${fileId}/download`, {
      responseType: 'blob'
    })
  },

  /**
   * 删除文件
   */
  deleteFile(fileId) {
    return http.delete(`/files/${fileId}`)
  },

  /**
   * 更新文件公开状态
   */
  updateFilePublicStatus(fileId, isPublic) {
    return http.put(`/files/${fileId}/public`, { is_public: isPublic })
  }
}