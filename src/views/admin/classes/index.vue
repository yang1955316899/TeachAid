<template>
  <div class="admin-classes">
    <!-- 页面标题和操作 -->
    <div class="page-header">
      <div class="header-left">
        <h1>班级管理</h1>
        <p>管理系统中的所有班级</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="$router.push('/admin/classes/create')">
          <el-icon><Plus /></el-icon>
          创建班级
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="searchForm" @submit.prevent="handleSearch">
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="班级名称或描述"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="年级">
          <el-select v-model="searchForm.grade_id" placeholder="选择年级" clearable style="width: 120px">
            <el-option
              v-for="grade in grades"
              :key="grade.id"
              :label="grade.name"
              :value="grade.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="选择状态" clearable style="width: 120px">
            <el-option label="正常" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 班级列表 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="classList"
        style="width: 100%"
      >
        <el-table-column prop="name" label="班级名称" width="150" />
        <el-table-column prop="description" label="班级描述" width="200" show-overflow-tooltip />
        <el-table-column prop="grade_name" label="年级" width="100" />
        <el-table-column prop="organization_name" label="所属机构" width="150" />
        <el-table-column prop="student_count" label="学生数" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.student_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="max_students" label="最大人数" width="80" align="center" />
        <el-table-column prop="teacher_count" label="教师数" width="80" align="center">
          <template #default="{ row }">
            <el-tag type="warning" size="small">{{ row.teacher_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag
              :type="row.is_active ? 'success' : 'danger'"
              size="small"
            >
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_time" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatTime(row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="info" size="small" @click="handleViewStudents(row)">
              学生管理
            </el-button>
            <el-button type="warning" size="small" @click="handleViewTeachers(row)">
              教师管理
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 编辑班级对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑班级"
      width="600px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
      >
        <el-form-item label="班级名称" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="班级描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="班级描述（可选）"
          />
        </el-form-item>
        <el-form-item label="年级" prop="grade_id">
          <el-select v-model="editForm.grade_id" placeholder="选择年级" style="width: 100%" clearable>
            <el-option
              v-for="grade in grades"
              :key="grade.id"
              :label="grade.name"
              :value="grade.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="最大人数" prop="max_students">
          <el-input-number
            v-model="editForm.max_students"
            :min="1"
            :max="200"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleEditSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 学生管理对话框 -->
    <el-dialog
      v-model="studentsDialogVisible"
      title="学生管理"
      width="800px"
    >
      <div class="students-header">
        <h4>{{ currentClass.name }} - 学生列表</h4>
        <el-button type="primary" size="small" @click="handleAddStudent">
          <el-icon><Plus /></el-icon>
          添加学生
        </el-button>
      </div>

      <el-table
        v-loading="studentsLoading"
        :data="classStudents"
        style="width: 100%"
        max-height="400"
      >
        <el-table-column prop="student_name" label="学生姓名" width="120" />
        <el-table-column prop="student_full_name" label="真实姓名" width="120" />
        <el-table-column prop="student_email" label="邮箱" width="200" />
        <el-table-column prop="joined_at" label="加入时间" width="150">
          <template #default="{ row }">
            {{ formatTime(row.joined_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              @click="handleRemoveStudent(row)"
            >
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

export default {
  name: 'AdminClasses',
  components: {
    Plus
  },
  setup() {
    const adminStore = useAdminStore()

    const loading = ref(false)
    const studentsLoading = ref(false)
    const classList = ref([])
    const classStudents = ref([])
    const grades = ref([])
    const editDialogVisible = ref(false)
    const studentsDialogVisible = ref(false)

    const searchForm = reactive({
      search: '',
      grade_id: '',
      is_active: ''
    })

    const pagination = reactive({
      page: 1,
      page_size: 20,
      total: 0
    })

    const editForm = reactive({
      id: '',
      name: '',
      description: '',
      grade_id: '',
      max_students: 50
    })

    const currentClass = reactive({
      id: '',
      name: ''
    })

    const editRules = {
      name: [
        { required: true, message: '请输入班级名称', trigger: 'blur' },
        { max: 100, message: '班级名称长度不能超过100个字符', trigger: 'blur' }
      ],
      max_students: [
        { required: true, message: '请输入最大人数', trigger: 'blur' },
        { type: 'number', min: 1, max: 200, message: '最大人数必须在1-200之间', trigger: 'blur' }
      ]
    }

    const loadClasses = async () => {
      loading.value = true
      try {
        const params = {
          page: pagination.page,
          page_size: pagination.page_size,
          ...searchForm
        }

        await adminStore.fetchClasses(params)
        classList.value = adminStore.classes.items
        pagination.total = adminStore.classes.total
      } catch (error) {
        ElMessage.error('加载班级列表失败')
      } finally {
        loading.value = false
      }
    }

    const loadGrades = async () => {
      // 模拟年级数据
      grades.value = [
        { id: '1', name: '一年级' },
        { id: '2', name: '二年级' },
        { id: '3', name: '三年级' },
        { id: '4', name: '四年级' },
        { id: '5', name: '五年级' },
        { id: '6', name: '六年级' }
      ]
    }

    const handleSearch = () => {
      pagination.page = 1
      loadClasses()
    }

    const handleReset = () => {
      Object.assign(searchForm, {
        search: '',
        grade_id: '',
        is_active: ''
      })
      handleSearch()
    }

    const handleSizeChange = (size) => {
      pagination.page_size = size
      pagination.page = 1
      loadClasses()
    }

    const handleCurrentChange = (page) => {
      pagination.page = page
      loadClasses()
    }

    const handleEdit = (row) => {
      Object.assign(editForm, {
        id: row.id,
        name: row.name,
        description: row.description,
        grade_id: row.grade_id,
        max_students: row.max_students
      })
      editDialogVisible.value = true
    }

    const handleEditSubmit = async () => {
      try {
        const { id, ...updateData } = editForm
        await adminStore.updateClass(id, updateData)
        ElMessage.success('班级更新成功')
        editDialogVisible.value = false
        loadClasses()
      } catch (error) {
        ElMessage.error('班级更新失败')
      }
    }

    const handleDelete = async (row) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除班级 "${row.name}" 吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await adminStore.deleteClass(row.id)
        ElMessage.success('班级删除成功')
        loadClasses()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('班级删除失败')
        }
      }
    }

    const handleViewStudents = async (row) => {
      currentClass.id = row.id
      currentClass.name = row.name
      studentsDialogVisible.value = true

      // 加载班级学生
      studentsLoading.value = true
      try {
        const response = await adminStore.adminApi.getClassStudents(row.id)
        classStudents.value = response.data.items
      } catch (error) {
        ElMessage.error('加载学生列表失败')
      } finally {
        studentsLoading.value = false
      }
    }

    const handleViewTeachers = (row) => {
      ElMessage.info('教师管理功能正在开发中')
    }

    const handleAddStudent = () => {
      ElMessage.info('添加学生功能正在开发中')
    }

    const handleRemoveStudent = async (student) => {
      try {
        await ElMessageBox.confirm(
          `确定要从班级中移除学生 "${student.student_name}" 吗？`,
          '确认移除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await adminStore.adminApi.removeStudentFromClass(currentClass.id, student.student_id)
        ElMessage.success('学生移除成功')

        // 重新加载学生列表
        handleViewStudents({ id: currentClass.id, name: currentClass.name })
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('移除学生失败')
        }
      }
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return '--'
      return new Date(timestamp).toLocaleString()
    }

    onMounted(() => {
      loadClasses()
      loadGrades()
    })

    return {
      loading,
      studentsLoading,
      classList,
      classStudents,
      grades,
      searchForm,
      pagination,
      editDialogVisible,
      studentsDialogVisible,
      editForm,
      currentClass,
      editRules,
      handleSearch,
      handleReset,
      handleSizeChange,
      handleCurrentChange,
      handleEdit,
      handleEditSubmit,
      handleDelete,
      handleViewStudents,
      handleViewTeachers,
      handleAddStudent,
      handleRemoveStudent,
      formatTime
    }
  }
}
</script>

<style scoped>
.admin-classes {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 20px;
}

.header-left h1 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.header-left p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.filter-card {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.students-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.students-header h4 {
  margin: 0;
  color: #303133;
}

:deep(.el-card__body) {
  padding: 20px;
}
</style>