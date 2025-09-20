/**
 * 笔记管理 API
 */
import { request } from '@/utils/http'

/**
 * 创建笔记
 * @param {Object} noteData 笔记数据
 * @returns {Promise}
 */
export function createNote(noteData) {
  return request({
    url: '/notes/',
    method: 'post',
    data: noteData
  })
}

/**
 * 获取笔记列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getNotes(params = {}) {
  return request({
    url: '/notes/',
    method: 'get',
    params: {
      category: params.category,
      subject: params.subject,
      is_starred: params.is_starred,
      is_archived: params.is_archived || false,
      search: params.search,
      sort_by: params.sort_by || 'created_time',
      sort_order: params.sort_order || 'desc',
      page: params.page || 1,
      size: params.size || 20
    }
  })
}

/**
 * 获取笔记详情
 * @param {string} noteId 笔记ID
 * @returns {Promise}
 */
export function getNoteDetail(noteId) {
  return request({
    url: `/notes/${noteId}`,
    method: 'get'
  })
}

/**
 * 更新笔记
 * @param {string} noteId 笔记ID
 * @param {Object} noteData 更新数据
 * @returns {Promise}
 */
export function updateNote(noteId, noteData) {
  return request({
    url: `/notes/${noteId}`,
    method: 'put',
    data: noteData
  })
}

/**
 * 删除笔记
 * @param {string} noteId 笔记ID
 * @returns {Promise}
 */
export function deleteNote(noteId) {
  return request({
    url: `/notes/${noteId}`,
    method: 'delete'
  })
}

/**
 * 从AI对话创建笔记
 * @param {string} sessionId 对话会话ID
 * @param {Object} noteData 笔记数据
 * @returns {Promise}
 */
export function createNoteFromChat(sessionId, noteData) {
  return request({
    url: `/notes/from-chat/${sessionId}`,
    method: 'post',
    data: noteData
  })
}

/**
 * 获取笔记统计摘要
 * @returns {Promise}
 */
export function getNotesSummary() {
  return request({
    url: '/notes/summary/stats',
    method: 'get'
  })
}

/**
 * 切换笔记收藏状态
 * @param {string} noteId 笔记ID
 * @returns {Promise}
 */
export function toggleNoteStar(noteId) {
  return request({
    url: `/notes/${noteId}/star`,
    method: 'put'
  })
}

/**
 * 切换笔记归档状态
 * @param {string} noteId 笔记ID
 * @returns {Promise}
 */
export function toggleNoteArchive(noteId) {
  return request({
    url: `/notes/${noteId}/archive`,
    method: 'put'
  })
}

/**
 * 笔记分类选项
 */
export const NOTE_CATEGORIES = [
  { value: 'general', label: '通用笔记' },
  { value: 'question', label: '题目笔记' },
  { value: 'chat', label: 'AI对话笔记' },
  { value: 'homework', label: '作业笔记' },
  { value: 'review', label: '复习笔记' },
  { value: 'summary', label: '总结笔记' },
  { value: 'mistake', label: '错题笔记' }
]

/**
 * 掌握程度选项
 */
export const MASTERY_LEVELS = [
  { value: 1, label: '完全不懂', color: '#f56565' },
  { value: 2, label: '基本理解', color: '#fd9c5c' },
  { value: 3, label: '理解一般', color: '#fbcb56' },
  { value: 4, label: '理解很好', color: '#68d391' },
  { value: 5, label: '完全掌握', color: '#38b2ac' }
]

/**
 * 难度等级选项
 */
export const DIFFICULTY_LEVELS = [
  { value: 'easy', label: '简单', color: '#68d391' },
  { value: 'medium', label: '中等', color: '#fbcb56' },
  { value: 'hard', label: '困难', color: '#f56565' }
]

/**
 * 排序选项
 */
export const SORT_OPTIONS = [
  { value: 'created_time', label: '创建时间' },
  { value: 'updated_time', label: '更新时间' },
  { value: 'last_reviewed_at', label: '最后复习时间' },
  { value: 'title', label: '标题' },
  { value: 'mastery_level', label: '掌握程度' },
  { value: 'review_count', label: '复习次数' }
]