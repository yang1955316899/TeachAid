<template>
  <div class="admin-permissions">
    <div class="header">
      <h2>权限管理</h2>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="角色管理" name="roles">
        <div class="tab-header">
          <el-button type="primary" @click="createRole">
            <el-icon><Plus /></el-icon>
            新建角色
          </el-button>
        </div>

        <el-table :data="roles" v-loading="loading">
          <el-table-column prop="name" label="角色名称" width="150" />
          <el-table-column prop="description" label="描述" width="200" />
          <el-table-column prop="userCount" label="用户数量" width="100" />
          <el-table-column prop="permissions" label="权限" min-width="300">
            <template #default="{ row }">
              <el-tag
                v-for="permission in row.permissions.slice(0, 3)"
                :key="permission"
                size="small"
                class="permission-tag"
              >
                {{ getPermissionText(permission) }}
              </el-tag>
              <el-tag v-if="row.permissions.length > 3" size="small" type="info">
                +{{ row.permissions.length - 3 }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="isSystem" label="系统角色" width="100">
            <template #default="{ row }">
              <el-tag :type="row.isSystem ? 'warning' : 'success'">
                {{ row.isSystem ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="editRole(row)">编辑</el-button>
              <el-button size="small" type="info" @click="viewRoleUsers(row)">用户</el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteRole(row)"
                :disabled="row.isSystem"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="权限列表" name="permissions">
        <el-tree
          :data="permissionTree"
          :props="treeProps"
          show-checkbox
          node-key="id"
          default-expand-all
          class="permission-tree"
        >
          <template #default="{ node, data }">
            <span class="tree-node">
              <span>{{ data.label }}</span>
              <span class="node-description">{{ data.description }}</span>
            </span>
          </template>
        </el-tree>
      </el-tab-pane>

      <el-tab-pane label="用户权限" name="user-permissions">
        <div class="user-permission-filters">
          <el-form :model="userFilters" layout="inline">
            <el-form-item label="用户">
              <el-select
                v-model="userFilters.userId"
                placeholder="选择用户"
                clearable
                filterable
              >
                <el-option
                  v-for="user in users"
                  :key="user.id"
                  :label="user.name"
                  :value="user.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="角色">
              <el-select v-model="userFilters.roleId" placeholder="选择角色" clearable>
                <el-option
                  v-for="role in roles"
                  :key="role.id"
                  :label="role.name"
                  :value="role.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="searchUserPermissions">搜索</el-button>
            </el-form-item>
          </el-form>
        </div>

        <el-table :data="userPermissions" v-loading="userPermissionLoading">
          <el-table-column prop="userName" label="用户" width="120" />
          <el-table-column prop="roleName" label="角色" width="120" />
          <el-table-column prop="permissions" label="权限" min-width="400">
            <template #default="{ row }">
              <el-tag
                v-for="permission in row.permissions"
                :key="permission"
                size="small"
                class="permission-tag"
              >
                {{ getPermissionText(permission) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="editUserPermissions(row)">编辑权限</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 角色编辑对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="isEditRole ? '编辑角色' : '新建角色'"
      width="600px"
    >
      <el-form :model="roleForm" :rules="roleRules" ref="roleFormRef" label-width="80px">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="roleForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="roleForm.description"
            type="textarea"
            rows="3"
            placeholder="请输入角色描述"
          />
        </el-form-item>
        <el-form-item label="权限">
          <el-tree
            ref="permissionTreeRef"
            :data="permissionTree"
            :props="treeProps"
            show-checkbox
            node-key="id"
            :default-checked-keys="roleForm.permissions"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRole" :loading="saving">
          {{ isEditRole ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const activeTab = ref('roles')
const loading = ref(false)
const userPermissionLoading = ref(false)
const saving = ref(false)

// 角色相关
const roles = ref([])
const roleDialogVisible = ref(false)
const isEditRole = ref(false)
const roleFormRef = ref()

const roleForm = reactive({
  id: '',
  name: '',
  description: '',
  permissions: []
})

const roleRules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入角色描述', trigger: 'blur' }]
}

// 权限树
const permissionTree = ref([])
const permissionTreeRef = ref()
const treeProps = {
  children: 'children',
  label: 'label'
}

// 用户权限
const users = ref([])
const userPermissions = ref([])
const userFilters = reactive({
  userId: '',
  roleId: ''
})

// 权限映射
const permissionMap = {
  'user:create': '创建用户',
  'user:edit': '编辑用户',
  'user:delete': '删除用户',
  'user:view': '查看用户',
  'class:create': '创建班级',
  'class:edit': '编辑班级',
  'class:delete': '删除班级',
  'class:view': '查看班级',
  'question:create': '创建题目',
  'question:edit': '编辑题目',
  'question:delete': '删除题目',
  'question:view': '查看题目',
  'homework:create': '创建作业',
  'homework:edit': '编辑作业',
  'homework:delete': '删除作业',
  'homework:view': '查看作业',
  'system:settings': '系统设置',
  'system:logs': '系统日志'
}

const getPermissionText = (permission) => {
  return permissionMap[permission] || permission
}

const loadRoles = async () => {
  loading.value = true
  try {
    // 模拟数据
    roles.value = [
      {
        id: '1',
        name: '超级管理员',
        description: '拥有所有权限',
        userCount: 1,
        permissions: ['user:create', 'user:edit', 'user:delete', 'system:settings'],
        isSystem: true
      },
      {
        id: '2',
        name: '教师',
        description: '普通教师权限',
        userCount: 15,
        permissions: ['question:create', 'homework:create', 'class:view'],
        isSystem: true
      },
      {
        id: '3',
        name: '学生',
        description: '学生权限',
        userCount: 120,
        permissions: ['homework:view'],
        isSystem: true
      }
    ]
  } finally {
    loading.value = false
  }
}

const loadPermissionTree = async () => {
  permissionTree.value = [
    {
      id: 'user',
      label: '用户管理',
      description: '用户相关权限',
      children: [
        { id: 'user:view', label: '查看用户', description: '查看用户列表和详情' },
        { id: 'user:create', label: '创建用户', description: '创建新用户' },
        { id: 'user:edit', label: '编辑用户', description: '编辑用户信息' },
        { id: 'user:delete', label: '删除用户', description: '删除用户' }
      ]
    },
    {
      id: 'class',
      label: '班级管理',
      description: '班级相关权限',
      children: [
        { id: 'class:view', label: '查看班级', description: '查看班级列表和详情' },
        { id: 'class:create', label: '创建班级', description: '创建新班级' },
        { id: 'class:edit', label: '编辑班级', description: '编辑班级信息' },
        { id: 'class:delete', label: '删除班级', description: '删除班级' }
      ]
    },
    {
      id: 'question',
      label: '题目管理',
      description: '题目相关权限',
      children: [
        { id: 'question:view', label: '查看题目', description: '查看题目列表和详情' },
        { id: 'question:create', label: '创建题目', description: '上传和创建题目' },
        { id: 'question:edit', label: '编辑题目', description: '编辑题目内容' },
        { id: 'question:delete', label: '删除题目', description: '删除题目' }
      ]
    },
    {
      id: 'homework',
      label: '作业管理',
      description: '作业相关权限',
      children: [
        { id: 'homework:view', label: '查看作业', description: '查看作业列表和详情' },
        { id: 'homework:create', label: '创建作业', description: '创建新作业' },
        { id: 'homework:edit', label: '编辑作业', description: '编辑作业内容' },
        { id: 'homework:delete', label: '删除作业', description: '删除作业' }
      ]
    },
    {
      id: 'system',
      label: '系统管理',
      description: '系统相关权限',
      children: [
        { id: 'system:settings', label: '系统设置', description: '修改系统配置' },
        { id: 'system:logs', label: '查看日志', description: '查看系统日志' },
        { id: 'system:backup', label: '数据备份', description: '备份和恢复数据' }
      ]
    }
  ]
}

const createRole = () => {
  isEditRole.value = false
  Object.assign(roleForm, {
    id: '',
    name: '',
    description: '',
    permissions: []
  })
  roleDialogVisible.value = true
}

const editRole = (row) => {
  isEditRole.value = true
  Object.assign(roleForm, row)
  roleDialogVisible.value = true
}

const saveRole = async () => {
  try {
    await roleFormRef.value.validate()

    // 获取选中的权限
    const checkedNodes = permissionTreeRef.value.getCheckedNodes()
    roleForm.permissions = checkedNodes.map(node => node.id).filter(id => !permissionTree.value.some(p => p.id === id))

    saving.value = true

    // TODO: 调用API保存角色
    await new Promise(resolve => setTimeout(resolve, 1000))

    ElMessage.success(isEditRole.value ? '角色更新成功' : '角色创建成功')
    roleDialogVisible.value = false
    loadRoles()
  } catch (error) {
    console.error('保存角色失败:', error)
  } finally {
    saving.value = false
  }
}

const deleteRole = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除角色"${row.name}"吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    // TODO: 调用API删除角色
    await new Promise(resolve => setTimeout(resolve, 500))

    ElMessage.success('角色删除成功')
    loadRoles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除角色失败')
    }
  }
}

const viewRoleUsers = (row) => {
  ElMessage.info('查看角色用户功能待实现')
}

const searchUserPermissions = async () => {
  userPermissionLoading.value = true
  try {
    // 模拟数据
    userPermissions.value = [
      {
        id: '1',
        userName: '张老师',
        roleName: '教师',
        permissions: ['question:create', 'homework:create', 'class:view']
      }
    ]
  } finally {
    userPermissionLoading.value = false
  }
}

const editUserPermissions = (row) => {
  ElMessage.info('编辑用户权限功能待实现')
}

onMounted(() => {
  loadRoles()
  loadPermissionTree()
})
</script>

<style scoped>
.admin-permissions {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.tab-header {
  margin-bottom: 20px;
}

.permission-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.permission-tree {
  max-height: 400px;
  overflow-y: auto;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.node-description {
  font-size: 12px;
  color: #999;
  margin-left: 10px;
}

.user-permission-filters {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 4px;
}
</style>