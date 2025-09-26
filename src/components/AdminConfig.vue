<template>
  <div class="admin-config">
    <el-tabs v-model="activeTab" class="config-tabs">
      <!-- 系统设置 -->
      <el-tab-pane label="系统设置" name="settings">
        <div class="tab-content">
          <div class="tab-header">
            <h3>系统设置管理</h3>
            <el-button
              type="primary"
              @click="showCreateSettingDialog = true"
              v-if="hasPermission('CREATE_SETTING')"
            >
              新增设置
            </el-button>
          </div>

          <div class="settings-content">
            <div v-for="(categorySettings, category) in groupedSettings" :key="category" class="setting-category">
              <h4>{{ getCategoryName(category) }}</h4>
              <el-table :data="categorySettings" stripe>
                <el-table-column prop="display_name" label="设置名称" width="200" />
                <el-table-column prop="setting_value" label="当前值" width="200">
                  <template #default="scope">
                    <el-tag v-if="scope.row.value_type === 'boolean'">
                      {{ scope.row.setting_value === 'true' ? '是' : '否' }}
                    </el-tag>
                    <span v-else>{{ scope.row.setting_value }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="描述" show-overflow-tooltip />
                <el-table-column label="操作" width="200">
                  <template #default="scope">
                    <el-button
                      size="small"
                      @click="editSetting(scope.row)"
                      :disabled="scope.row.is_readonly"
                    >
                      编辑
                    </el-button>
                    <el-button
                      size="small"
                      type="danger"
                      @click="deleteSetting(scope.row)"
                      v-if="!scope.row.is_readonly && hasPermission('DELETE_SETTING')"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 安全策略 -->
      <el-tab-pane label="安全策略" name="security">
        <div class="tab-content">
          <div class="tab-header">
            <h3>安全策略管理</h3>
            <el-button
              type="primary"
              @click="showCreatePolicyDialog = true"
              v-if="hasPermission('CREATE_POLICY')"
            >
              新增策略
            </el-button>
          </div>

          <el-table :data="securityPolicies" stripe>
            <el-table-column prop="policy_name" label="策略名称" width="200" />
            <el-table-column prop="policy_type" label="策略类型" width="150">
              <template #default="scope">
                <el-tag :type="getPolicyTypeColor(scope.row.policy_type)">
                  {{ getPolicyTypeName(scope.row.policy_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column prop="priority" label="优先级" width="100" />
            <el-table-column label="适用范围" width="200">
              <template #default="scope">
                <div>
                  <el-tag v-for="role in scope.row.applies_to_roles" :key="role" size="small" style="margin: 2px;">
                    {{ getRoleName(role) }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button size="small" @click="editPolicy(scope.row)">编辑</el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="deletePolicy(scope.row)"
                  :disabled="scope.row.is_system"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 登录日志 -->
      <el-tab-pane label="登录日志" name="logs">
        <div class="tab-content">
          <div class="tab-header">
            <h3>登录日志</h3>
            <div class="header-controls">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                @change="loadLoginLogs"
              />
              <el-select v-model="logFilters.is_success" placeholder="登录状态" clearable @change="loadLoginLogs">
                <el-option label="成功" :value="true" />
                <el-option label="失败" :value="false" />
              </el-select>
              <el-button @click="exportLogs">导出日志</el-button>
            </div>
          </div>

          <!-- 统计卡片 -->
          <div class="stats-cards">
            <el-card class="stat-card">
              <div class="stat-item">
                <div class="stat-number">{{ loginStats.total_logins }}</div>
                <div class="stat-label">总登录次数</div>
              </div>
            </el-card>
            <el-card class="stat-card">
              <div class="stat-item">
                <div class="stat-number">{{ loginStats.successful_logins }}</div>
                <div class="stat-label">成功登录</div>
              </div>
            </el-card>
            <el-card class="stat-card">
              <div class="stat-item">
                <div class="stat-number">{{ loginStats.failed_logins }}</div>
                <div class="stat-label">失败登录</div>
              </div>
            </el-card>
            <el-card class="stat-card">
              <div class="stat-item">
                <div class="stat-number">{{ securityStats.locked_users }}</div>
                <div class="stat-label">锁定用户</div>
              </div>
            </el-card>
          </div>

          <!-- 登录日志表格 -->
          <el-table :data="loginLogs" stripe>
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column prop="email" label="邮箱" width="200" show-overflow-tooltip />
            <el-table-column label="登录状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.is_success ? 'success' : 'danger'">
                  {{ scope.row.is_success ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="ip_address" label="IP地址" width="120" />
            <el-table-column prop="failure_reason" label="失败原因" show-overflow-tooltip />
            <el-table-column prop="logged_in_at" label="登录时间" width="180">
              <template #default="scope">
                {{ formatDateTime(scope.row.logged_in_at) }}
              </template>
            </el-table-column>
            <el-table-column label="风险评分" width="100">
              <template #default="scope">
                <el-tag v-if="scope.row.risk_score" :type="getRiskScoreColor(scope.row.risk_score)">
                  {{ scope.row.risk_score }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <el-pagination
            v-model:current-page="logPagination.page"
            v-model:page-size="logPagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="logPagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadLoginLogs"
            @current-change="loadLoginLogs"
          />
        </div>
      </el-tab-pane>

      <!-- 用户管理 -->
      <el-tab-pane label="用户管理" name="users">
        <div class="tab-content">
          <div class="tab-header">
            <h3>用户管理</h3>
            <div class="header-controls">
              <el-input
                v-model="userFilters.search"
                placeholder="搜索用户名、邮箱或姓名"
                @input="loadUsers"
                clearable
              />
              <el-select v-model="userFilters.role" placeholder="用户角色" clearable @change="loadUsers">
                <el-option label="管理员" value="admin" />
                <el-option label="教师" value="teacher" />
                <el-option label="学生" value="student" />
              </el-select>
              <el-select v-model="userFilters.status" placeholder="用户状态" clearable @change="loadUsers">
                <el-option label="激活" value="active" />
                <el-option label="未激活" value="inactive" />
                <el-option label="锁定" value="locked" />
                <el-option label="暂停" value="suspended" />
              </el-select>
            </div>
          </div>

          <el-table :data="users" stripe>
            <el-table-column prop="user_name" label="用户名" width="120" />
            <el-table-column prop="user_email" label="邮箱" width="200" show-overflow-tooltip />
            <el-table-column prop="user_full_name" label="姓名" width="120" />
            <el-table-column label="角色" width="100">
              <template #default="scope">
                <el-tag :type="getRoleColor(scope.row.user_role)">
                  {{ getRoleName(scope.row.user_role) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getStatusColor(scope.row.user_status)">
                  {{ getStatusName(scope.row.user_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="user_failed_login_attempts" label="失败次数" width="100" />
            <el-table-column prop="user_last_login_time" label="最后登录" width="180">
              <template #default="scope">
                {{ formatDateTime(scope.row.user_last_login_time) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-dropdown>
                  <el-button size="small">
                    操作 <el-icon><arrow-down /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="changeUserStatus(scope.row, 'active')" v-if="scope.row.user_status !== 'active'">
                        激活
                      </el-dropdown-item>
                      <el-dropdown-item @click="changeUserStatus(scope.row, 'suspended')" v-if="scope.row.user_status === 'active'">
                        暂停
                      </el-dropdown-item>
                      <el-dropdown-item @click="unlockUser(scope.row)" v-if="scope.row.user_status === 'locked'">
                        解锁
                      </el-dropdown-item>
                      <el-dropdown-item @click="resetPassword(scope.row)">
                        重置密码
                      </el-dropdown-item>
                      <el-dropdown-item @click="viewUserDetails(scope.row)">
                        查看详情
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <el-pagination
            v-model:current-page="userPagination.page"
            v-model:page-size="userPagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="userPagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadUsers"
            @current-change="loadUsers"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建设置对话框 -->
    <el-dialog v-model="showCreateSettingDialog" title="新增系统设置" width="600px">
      <el-form :model="newSetting" :rules="settingRules" ref="settingForm" label-width="120px">
        <el-form-item label="分类" prop="category">
          <el-select v-model="newSetting.category" placeholder="选择或输入分类" filterable allow-create>
            <el-option v-for="cat in settingCategories" :key="cat.value" :label="cat.label" :value="cat.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="设置键名" prop="setting_key">
          <el-input v-model="newSetting.setting_key" placeholder="英文键名，如 max_login_attempts" />
        </el-form-item>
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="newSetting.display_name" placeholder="用户界面显示的名称" />
        </el-form-item>
        <el-form-item label="值类型" prop="value_type">
          <el-select v-model="newSetting.value_type">
            <el-option label="字符串" value="string" />
            <el-option label="数字" value="number" />
            <el-option label="布尔值" value="boolean" />
            <el-option label="JSON对象" value="json" />
          </el-select>
        </el-form-item>
        <el-form-item label="设置值" prop="setting_value">
          <el-input v-model="newSetting.setting_value" placeholder="设置的值" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="newSetting.description" type="textarea" placeholder="设置的描述信息" />
        </el-form-item>
        <el-form-item label="输入类型" prop="input_type">
          <el-select v-model="newSetting.input_type">
            <el-option label="文本输入" value="text" />
            <el-option label="数字输入" value="number" />
            <el-option label="选择框" value="select" />
            <el-option label="开关" value="switch" />
            <el-option label="多行文本" value="textarea" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateSettingDialog = false">取消</el-button>
        <el-button type="primary" @click="createSetting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑设置对话框 -->
    <el-dialog v-model="showEditSettingDialog" title="编辑系统设置" width="600px">
      <el-form :model="editingSetting" ref="editSettingForm" label-width="120px">
        <el-form-item label="显示名称">
          <el-input v-model="editingSetting.display_name" />
        </el-form-item>
        <el-form-item label="设置值">
          <el-input v-if="editingSetting.input_type === 'text'" v-model="editingSetting.setting_value" />
          <el-input-number v-else-if="editingSetting.input_type === 'number'" v-model="editingSetting.setting_value" />
          <el-switch v-else-if="editingSetting.input_type === 'switch'" v-model="editingSetting.setting_value" />
          <el-select v-else-if="editingSetting.input_type === 'select'" v-model="editingSetting.setting_value">
            <el-option v-for="opt in editingSetting.options?.options || []" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
          <el-input v-else v-model="editingSetting.setting_value" type="textarea" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editingSetting.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditSettingDialog = false">取消</el-button>
        <el-button type="primary" @click="updateSetting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// 响应式数据
const activeTab = ref('settings')
const settings = ref({})
const securityPolicies = ref([])
const loginLogs = ref([])
const users = ref([])

const loginStats = ref({
  total_logins: 0,
  successful_logins: 0,
  failed_logins: 0,
  unique_users: 0
})

const securityStats = ref({
  locked_users: 0,
  failed_attempts_today: 0,
  suspicious_ips: []
})

// 对话框状态
const showCreateSettingDialog = ref(false)
const showEditSettingDialog = ref(false)
const showCreatePolicyDialog = ref(false)

// 表单数据
const newSetting = reactive({
  category: '',
  setting_key: '',
  display_name: '',
  value_type: 'string',
  setting_value: '',
  description: '',
  input_type: 'text'
})

const editingSetting = ref({})

// 筛选和分页
const dateRange = ref([])
const logFilters = reactive({
  is_success: null
})

const userFilters = reactive({
  search: '',
  role: '',
  status: ''
})

const logPagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const userPagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 计算属性
const groupedSettings = computed(() => {
  return settings.value
})

// 设置分类
const settingCategories = [
  { label: '安全设置', value: 'security' },
  { label: '系统设置', value: 'system' },
  { label: '邮件设置', value: 'email' },
  { label: '文件设置', value: 'file' },
  { label: 'AI设置', value: 'ai' }
]

// 表单验证规则
const settingRules = {
  category: [{ required: true, message: '请选择设置分类', trigger: 'change' }],
  setting_key: [{ required: true, message: '请输入设置键名', trigger: 'blur' }],
  display_name: [{ required: true, message: '请输入显示名称', trigger: 'blur' }],
  setting_value: [{ required: true, message: '请输入设置值', trigger: 'blur' }]
}

// 方法
const hasPermission = (permission) => {
  return userStore.user?.user_role === 'admin'
}

const getCategoryName = (category) => {
  const categoryMap = {
    security: '安全设置',
    system: '系统设置',
    email: '邮件设置',
    file: '文件设置',
    ai: 'AI设置'
  }
  return categoryMap[category] || category
}

const getPolicyTypeColor = (type) => {
  const colorMap = {
    login_security: 'warning',
    password_policy: 'info',
    session_management: 'success',
    access_control: 'danger'
  }
  return colorMap[type] || ''
}

const getPolicyTypeName = (type) => {
  const nameMap = {
    login_security: '登录安全',
    password_policy: '密码策略',
    session_management: '会话管理',
    access_control: '访问控制'
  }
  return nameMap[type] || type
}

const getRoleName = (role) => {
  const roleMap = {
    admin: '管理员',
    teacher: '教师',
    student: '学生'
  }
  return roleMap[role] || role
}

const getRoleColor = (role) => {
  const colorMap = {
    admin: 'danger',
    teacher: 'warning',
    student: 'info'
  }
  return colorMap[role] || ''
}

const getStatusName = (status) => {
  const statusMap = {
    active: '激活',
    inactive: '未激活',
    locked: '锁定',
    suspended: '暂停'
  }
  return statusMap[status] || status
}

const getStatusColor = (status) => {
  const colorMap = {
    active: 'success',
    inactive: 'info',
    locked: 'danger',
    suspended: 'warning'
  }
  return colorMap[status] || ''
}

const getRiskScoreColor = (score) => {
  if (score >= 8) return 'danger'
  if (score >= 5) return 'warning'
  return 'success'
}

const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  return new Date(datetime).toLocaleString('zh-CN')
}

// API调用方法
const loadSettings = async () => {
  try {
    const response = await fetch('/api/admin/settings')
    const data = await response.json()
    settings.value = data.settings
  } catch (error) {
    ElMessage.error('加载系统设置失败')
  }
}

const loadSecurityPolicies = async () => {
  try {
    const response = await fetch('/api/admin/security-policies')
    const data = await response.json()
    securityPolicies.value = data.policies
  } catch (error) {
    ElMessage.error('加载安全策略失败')
  }
}

const loadLoginLogs = async () => {
  try {
    const params = new URLSearchParams({
      page: logPagination.page,
      page_size: logPagination.pageSize
    })

    if (dateRange.value && dateRange.value.length === 2) {
      params.append('start_date', dateRange.value[0].toISOString())
      params.append('end_date', dateRange.value[1].toISOString())
    }

    if (logFilters.is_success !== null) {
      params.append('is_success', logFilters.is_success)
    }

    const response = await fetch(`/api/admin/login-logs?${params}`)
    const data = await response.json()
    loginLogs.value = data.logs
    logPagination.total = data.total
  } catch (error) {
    ElMessage.error('加载登录日志失败')
  }
}

const loadLoginStats = async () => {
  try {
    const response = await fetch('/api/admin/login-stats')
    const data = await response.json()
    loginStats.value = data
  } catch (error) {
    ElMessage.error('加载登录统计失败')
  }
}

const loadSecurityStats = async () => {
  try {
    const response = await fetch('/api/admin/security-stats')
    const data = await response.json()
    securityStats.value = data
  } catch (error) {
    ElMessage.error('加载安全统计失败')
  }
}

const loadUsers = async () => {
  try {
    const params = new URLSearchParams({
      page: userPagination.page,
      page_size: userPagination.pageSize
    })

    if (userFilters.search) {
      params.append('search', userFilters.search)
    }
    if (userFilters.role) {
      params.append('role', userFilters.role)
    }
    if (userFilters.status) {
      params.append('status', userFilters.status)
    }

    const response = await fetch(`/api/admin/users?${params}`)
    const data = await response.json()
    users.value = data.users
    userPagination.total = data.total
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  }
}

// 设置管理方法
const createSetting = async () => {
  try {
    const response = await fetch('/api/admin/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newSetting)
    })

    if (response.ok) {
      ElMessage.success('设置创建成功')
      showCreateSettingDialog.value = false
      Object.assign(newSetting, {
        category: '',
        setting_key: '',
        display_name: '',
        value_type: 'string',
        setting_value: '',
        description: '',
        input_type: 'text'
      })
      await loadSettings()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '创建设置失败')
    }
  } catch (error) {
    ElMessage.error('创建设置失败')
  }
}

const editSetting = (setting) => {
  editingSetting.value = { ...setting }
  showEditSettingDialog.value = true
}

const updateSetting = async () => {
  try {
    const response = await fetch(`/api/admin/settings/${editingSetting.value.system_id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editingSetting.value)
    })

    if (response.ok) {
      ElMessage.success('设置更新成功')
      showEditSettingDialog.value = false
      await loadSettings()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '更新设置失败')
    }
  } catch (error) {
    ElMessage.error('更新设置失败')
  }
}

// 用户管理方法
const changeUserStatus = async (user, status) => {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      `确定要将用户 ${user.user_name} 的状态更改为 ${getStatusName(status)} 吗？`,
      '更改用户状态',
      {
        inputPlaceholder: '请输入操作原因（可选）'
      }
    )

    const response = await fetch(`/api/admin/users/${user.user_id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, reason })
    })

    if (response.ok) {
      ElMessage.success('用户状态更新成功')
      await loadUsers()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '更新用户状态失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('更新用户状态失败')
    }
  }
}

const unlockUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要解锁用户 ${user.user_name} 吗？`,
      '解锁用户',
      { type: 'warning' }
    )

    const response = await fetch(`/api/admin/users/${user.user_id}/unlock`, {
      method: 'POST'
    })

    if (response.ok) {
      ElMessage.success('用户解锁成功')
      await loadUsers()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '解锁用户失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('解锁用户失败')
    }
  }
}

// 初始化
onMounted(() => {
  loadSettings()
  loadSecurityPolicies()
  loadLoginLogs()
  loadLoginStats()
  loadSecurityStats()
  loadUsers()
})
</script>

<style scoped>
.admin-config {
  padding: 20px;
}

.config-tabs {
  height: 100%;
}

.tab-content {
  padding: 20px 0;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.tab-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.settings-content {
  max-width: 100%;
}

.setting-category {
  margin-bottom: 30px;
}

.setting-category h4 {
  margin: 0 0 15px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e4e7ed;
  font-size: 16px;
  font-weight: 600;
  color: #606266;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 20px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.el-table {
  margin-bottom: 20px;
}

.el-pagination {
  text-align: center;
  margin-top: 20px;
}
</style>