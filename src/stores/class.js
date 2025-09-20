import { defineStore } from 'pinia'
import { classApi } from '@/api/class'
import { message } from 'ant-design-vue'

export const useClassStore = defineStore('class', {
  state: () => ({
    classes: [],
    currentClass: null,
    loading: false,
    pagination: {
      current: 1,
      pageSize: 10,
      total: 0,
      pages: 0
    }
  }),
  
  getters: {
    classCount: (state) => state.classes.length,
    classesByGrade: (state) => {
      return (grade) => state.classes.filter(c => c.grade === grade)
    }
  },
  
  actions: {
    /**
     * 获取班级列表
     */
    async fetchClasses(params = {}) {
      this.loading = true
      try {
        const response = await classApi.getClasses(params)
        // 兼容 BaseResponse 与直接分页响应两种结构
        let items, page, size, total, pages, success = true
        if (response && Object.prototype.hasOwnProperty.call(response, 'success')) {
          success = !!response.success
          if (!success) throw new Error(response.message || '获取班级列表失败')
          const d = response.data || {}
          items = d.items || []
          page = d.page || 1
          size = d.size || this.pagination.pageSize
          total = d.total || 0
          pages = d.pages || 0
        } else {
          items = response?.items || []
          page = response?.page || 1
          size = response?.size || this.pagination.pageSize
          total = response?.total || 0
          pages = response?.pages || 0
        }
        this.classes = items
        this.pagination = {
          current: page,
          pageSize: size,
          total,
          pages
        }
        return response
      } catch (error) {
        console.error('获取班级失败:', error)
        message.error('获取班级列表失败')
        this.classes = []
        return { success: false, message: error?.message || '获取班级列表失败' }
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取班级详情
     */
    async fetchClass(id) {
      this.loading = true
      try {
        const response = await classApi.getClass(id)
        if (response.success) {
          this.currentClass = response.data
          return response.data
        } else {
          throw new Error(response.message || '获取班级详情失败')
        }
      } catch (error) {
        console.error('获取班级详情失败:', error)
        message.error('获取班级详情失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 创建班级
     */
    async createClass(data) {
      this.loading = true
      try {
        const response = await classApi.createClass(data)
        if (response.success) {
          message.success('班级创建成功')
          return response.data
        } else {
          throw new Error(response.message || '创建班级失败')
        }
      } catch (error) {
        console.error('创建班级失败:', error)
        message.error('创建班级失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 更新班级
     */
    async updateClass(id, data) {
      this.loading = true
      try {
        const response = await classApi.updateClass(id, data)
        if (response.success) {
          message.success('班级更新成功')
          // 更新本地数据
          const index = this.classes.findIndex(c => c.id === id)
          if (index !== -1) {
            this.classes[index] = { ...this.classes[index], ...data }
          }
          if (this.currentClass && this.currentClass.id === id) {
            this.currentClass = { ...this.currentClass, ...data }
          }
          return response.data
        } else {
          throw new Error(response.message || '更新班级失败')
        }
      } catch (error) {
        console.error('更新班级失败:', error)
        message.error('更新班级失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 删除班级
     */
    async deleteClass(id) {
      this.loading = true
      try {
        const response = await classApi.deleteClass(id)
        if (response.success) {
          message.success('班级删除成功')
          // 从本地数据中移除
          this.classes = this.classes.filter(c => c.id !== id)
          if (this.currentClass && this.currentClass.id === id) {
            this.currentClass = null
          }
          return response
        } else {
          throw new Error(response.message || '删除班级失败')
        }
      } catch (error) {
        console.error('删除班级失败:', error)
        message.error('删除班级失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 添加学生到班级
     */
    async addStudentToClass(classId, studentData) {
      try {
        const response = await classApi.addStudent(classId, studentData)
        if (response.success) {
          message.success('学生添加成功')
          return response.data
        } else {
          throw new Error(response.message || '添加学生失败')
        }
      } catch (error) {
        console.error('添加学生失败:', error)
        message.error('添加学生失败')
        throw error
      }
    },

    /**
     * 从班级移除学生
     */
    async removeStudentFromClass(classId, studentId) {
      try {
        const response = await classApi.removeStudent(classId, studentId)
        if (response.success) {
          message.success('学生移除成功')
          return response.data
        } else {
          throw new Error(response.message || '移除学生失败')
        }
      } catch (error) {
        console.error('移除学生失败:', error)
        message.error('移除学生失败')
        throw error
      }
    },

    /**
     * 获取班级学生列表
     */
    async fetchClassStudents(classId) {
      try {
        const response = await classApi.getClassStudents(classId)
        if (response.success) {
          return response.data
        } else {
          throw new Error(response.message || '获取学生列表失败')
        }
      } catch (error) {
        console.error('获取学生列表失败:', error)
        message.error('获取学生列表失败')
        throw error
      }
    },

    /**
     * 设置当前班级
     */
    setCurrentClass(classInfo) {
      this.currentClass = classInfo
    },

    /**
     * 清空班级列表
     */
    clearClasses() {
      this.classes = []
      this.currentClass = null
      this.pagination = {
        current: 1,
        pageSize: 10,
        total: 0,
        pages: 0
      }
    }
  }
})
