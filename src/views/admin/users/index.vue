<template>
  <div class="admin-users">
    <!-- 页面标题和操作 -->
    <div class="page-header">
      <div class="header-left">
        <h1>用户管理</h1>
        <p>管理系统中的所有用户</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="$router.push('/admin/users/create')">
          <el-icon><Plus /></el-icon>
          创建用户
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="searchForm" @submit.prevent="handleSearch">
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="用户名、邮箱或姓名"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="searchForm.role" placeholder="选择角色" clearable style="width: 120px">
            <el-option label="管理员" value="admin" />
            <el-option label="教师" value="teacher" />
            <el-option label="学生" value="student" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="选择状态" clearable style="width: 120px">
            <el-option label="正常" value="active" />
            <el-option label="禁用" value="inactive" />
            <el-option label="锁定" value="locked" />
            <el-option label="挂起" value="suspended" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="userList"
        style="width: 100%"
        stripe
        border
        size="default"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column prop="user_name" label="用户名" min-width="120" show-overflow-tooltip />
        <el-table-column prop="user_email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column prop="user_full_name" label="真实姓名" min-width="100" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.user_full_name || '--' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="user_role" label="角色" width="80" align="center">
          <template #default="{ row }">
            <el-tag
              :type="getRoleTagType(row.user_role)"
              size="small"
              effect="plain"
            >
              {{ getRoleText(row.user_role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="user_status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag
              :type="getStatusTagType(row.user_status)"
              size="small"
              effect="plain"
            >
              {{ getStatusText(row.user_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="organization_name" label="所属机构" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.organization_name || '--' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="user_login_count" label="登录次数" width="90" align="center">
          <template #default="{ row }">
            <span class="login-count">{{ row.user_login_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="user_last_login_time" label="最后登录" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.user_last_login_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_time" label="创建时间" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.created_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                type="info"
                size="small"
                @click="handleEdit(row)"
                :icon="Edit"
              >
                编辑
              </el-button>
              <el-button
                type="warning"
                size="small"
                plain
                @click="handleResetPassword(row)"
                :icon="Key"
              >
                重置密码
              </el-button>
              <el-button
                v-if="row.user_id !== currentUser.user_id"
                type="danger"
                size="small"
                plain
                @click="handleDelete(row)"
                :icon="Delete"
              >
                删除
              </el-button>
            </div>
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
          background
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 编辑用户对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑用户"
      width="600px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="user_name">
          <el-input v-model="editForm.user_name" disabled />
        </el-form-item>
        <el-form-item label="邮箱" prop="user_email">
          <el-input v-model="editForm.user_email" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="user_full_name">
          <el-input v-model="editForm.user_full_name" />
        </el-form-item>
        <el-form-item label="角色" prop="user_role">
          <el-select v-model="editForm.user_role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="教师" value="teacher" />
            <el-option label="学生" value="student" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="user_status">
          <el-select v-model="editForm.user_status" style="width: 100%">
            <el-option label="正常" value="active" />
            <el-option label="禁用" value="inactive" />
            <el-option label="锁定" value="locked" />
            <el-option label="挂起" value="suspended" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleEditSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog
      v-model="resetPasswordDialogVisible"
      title="重置密码"
      width="400px"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
      >
        <el-form-item label="用户" prop="user_name">
          <el-input v-model="passwordForm.user_name" disabled />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            show-password
            placeholder="请输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="resetPasswordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handlePasswordSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Key, Delete } from '@element-plus/icons-vue'

export default {
  name: 'AdminUsers',
  components: {
    Plus,
    Edit,
    Key,
    Delete
  },
  setup() {
    const adminStore = useAdminStore()
    const authStore = useAuthStore()

    const loading = ref(false)
    const userList = ref([])
    const editDialogVisible = ref(false)
    const resetPasswordDialogVisible = ref(false)

    const searchForm = reactive({
      search: '',
      role: '',
      status: ''
    })

    const pagination = reactive({
      page: 1,
      page_size: 20,
      total: 0
    })

    const editForm = reactive({
      user_id: '',
      user_name: '',
      user_email: '',
      user_full_name: '',
      user_role: '',
      user_status: ''
    })

    const passwordForm = reactive({
      user_id: '',
      user_name: '',
      new_password: ''
    })

    const editRules = {
      user_email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
      ],
      user_role: [
        { required: true, message: '请选择角色', trigger: 'change' }
      ],
      user_status: [
        { required: true, message: '请选择状态', trigger: 'change' }
      ]
    }

    const passwordRules = {
      new_password: [
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
      ]
    }

    const loadUsers = async () => {
      loading.value = true
      try {
        const params = {
          page: pagination.page,
          page_size: pagination.page_size,
          ...searchForm
        }

        const response = await adminStore.fetchUsers(params)
        userList.value = adminStore.users.items
        pagination.total = adminStore.users.total
      } catch (error) {
        console.error('加载用户列表失败:', error)
        ElMessage.error('加载用户列表失败')
      } finally {
        loading.value = false
      }
    }

    const handleSearch = () => {
      pagination.page = 1
      loadUsers()
    }

    const handleReset = () => {
      Object.assign(searchForm, {
        search: '',
        role: '',
        status: ''
      })
      handleSearch()
    }

    const handleSizeChange = (size) => {
      pagination.page_size = size
      pagination.page = 1
      loadUsers()
    }

    const handleCurrentChange = (page) => {
      pagination.page = page
      loadUsers()
    }

    const handleEdit = (row) => {
      Object.assign(editForm, {
        user_id: row.user_id,
        user_name: row.user_name,
        user_email: row.user_email,
        user_full_name: row.user_full_name,
        user_role: row.user_role,
        user_status: row.user_status
      })
      editDialogVisible.value = true
    }

    const handleEditSubmit = async () => {
      try {
        const { user_id, user_name, ...updateData } = editForm
        await adminStore.updateUser(user_id, updateData)
        ElMessage.success('用户更新成功')
        editDialogVisible.value = false
        loadUsers()
      } catch (error) {
        ElMessage.error('用户更新失败')
      }
    }

    const handleResetPassword = (row) => {
      Object.assign(passwordForm, {
        user_id: row.user_id,
        user_name: row.user_name,
        new_password: ''
      })
      resetPasswordDialogVisible.value = true
    }

    const handlePasswordSubmit = async () => {
      try {
        await adminStore.resetUserPassword(passwordForm.user_id, passwordForm.new_password)
        ElMessage.success('密码重置成功')
        resetPasswordDialogVisible.value = false
      } catch (error) {
        ElMessage.error('密码重置失败')
      }
    }

    const handleDelete = async (row) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除用户 "${row.user_name}" 吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await adminStore.deleteUser(row.user_id)
        ElMessage.success('用户删除成功')
        loadUsers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('用户删除失败')
        }
      }
    }

    const getRoleText = (role) => {
      const roleMap = {
        admin: '管理员',
        teacher: '教师',
        student: '学生'
      }
      return roleMap[role] || role
    }

    const getRoleTagType = (role) => {
      const typeMap = {
        admin: 'danger',
        teacher: 'warning',
        student: 'primary'
      }
      return typeMap[role] || 'info'
    }

    const getStatusText = (status) => {
      const statusMap = {
        active: '正常',
        inactive: '禁用',
        locked: '锁定',
        suspended: '挂起'
      }
      return statusMap[status] || status
    }

    const getStatusTagType = (status) => {
      const typeMap = {
        active: 'success',
        inactive: 'info',
        locked: 'danger',
        suspended: 'warning'
      }
      return typeMap[status] || 'info'
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return '--'
      return new Date(timestamp).toLocaleString()
    }

    onMounted(() => {
      loadUsers()
    })

    return {
      loading,
      userList,
      searchForm,
      pagination,
      editDialogVisible,
      resetPasswordDialogVisible,
      editForm,
      passwordForm,
      editRules,
      passwordRules,
      currentUser: authStore.userInfo,
      handleSearch,
      handleReset,
      handleSizeChange,
      handleCurrentChange,
      handleEdit,
      handleEditSubmit,
      handleResetPassword,
      handlePasswordSubmit,
      handleDelete,
      getRoleText,
      getRoleTagType,
      getStatusText,
      getStatusTagType,
      formatTime,
      Edit,
      Key,
      Delete
    }
  }
}
</script>

<style scoped>
.admin-users {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 20px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
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
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
}

.table-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 16px 0;
  border-top: 1px solid #f0f0f0;
}

.action-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: nowrap;
  justify-content: center;
  align-items: center;
}

.action-buttons .el-button {
  padding: 4px 6px;
  font-size: 12px;
  min-width: 60px;
  flex-shrink: 0;
}

.login-count {
  font-weight: 600;
  color: #409eff;
}

.time-text {
  font-size: 12px;
  color: #606266;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}

:deep(.el-table th) {
  background-color: #fafafa !important;
  border-bottom: 2px solid #e4e7ed;
  font-weight: 600;
  color: #606266;
}

:deep(.el-table td) {
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #fafbfc;
}

:deep(.el-table__body tr:hover td) {
  background-color: #f5f7fa !important;
}

:deep(.el-tag) {
  font-weight: 500;
}

:deep(.el-form--inline .el-form-item) {
  margin-right: 20px;
  margin-bottom: 12px;
}

:deep(.el-input) {
  border-radius: 4px;
}

:deep(.el-select) {
  border-radius: 4px;
}

:deep(.el-button) {
  border-radius: 4px;
  font-weight: 500;
}

:deep(.el-button--primary) {
  background-color: #409eff;
  border-color: #409eff;
}

:deep(.el-button--primary:hover) {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

:deep(.el-dialog) {
  border-radius: 8px;
}

:deep(.el-dialog__header) {
  background-color: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 20px;
}

:deep(.el-dialog__title) {
  font-weight: 600;
  color: #303133;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}
</style>