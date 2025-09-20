<template>
  <div class="admin-create-user">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>创建用户</h1>
      <p>添加新的用户到系统中</p>
    </div>

    <!-- 创建表单 -->
    <el-card>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        style="max-width: 600px"
      >
        <el-form-item label="用户名" prop="user_name">
          <el-input
            v-model="form.user_name"
            placeholder="请输入用户名"
            :prefix-icon="User"
          />
          <div class="form-tip">用户名用于登录，创建后不可修改</div>
        </el-form-item>

        <el-form-item label="邮箱" prop="user_email">
          <el-input
            v-model="form.user_email"
            placeholder="请输入邮箱"
            :prefix-icon="Message"
          />
          <div class="form-tip">邮箱地址用于接收通知和密码重置</div>
        </el-form-item>

        <el-form-item label="密码" prop="user_password">
          <el-input
            v-model="form.user_password"
            type="password"
            show-password
            placeholder="请输入密码"
            :prefix-icon="Lock"
          />
          <div class="form-tip">密码长度至少6位</div>
        </el-form-item>

        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="form.confirm_password"
            type="password"
            show-password
            placeholder="请再次输入密码"
            :prefix-icon="Lock"
          />
        </el-form-item>

        <el-form-item label="真实姓名" prop="user_full_name">
          <el-input
            v-model="form.user_full_name"
            placeholder="请输入真实姓名（可选）"
          />
        </el-form-item>

        <el-form-item label="用户角色" prop="user_role">
          <el-select v-model="form.user_role" placeholder="请选择用户角色" style="width: 100%">
            <el-option
              label="管理员"
              value="admin"
              :disabled="!canCreateAdmin"
            >
              <span>管理员</span>
              <span style="float: right; color: #8492a6; font-size: 13px">
                系统最高权限
              </span>
            </el-option>
            <el-option label="教师" value="teacher">
              <span>教师</span>
              <span style="float: right; color: #8492a6; font-size: 13px">
                可以创建和管理课程
              </span>
            </el-option>
            <el-option label="学生" value="student">
              <span>学生</span>
              <span style="float: right; color: #8492a6; font-size: 13px">
                参与学习和作业
              </span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="所属机构" prop="organization_id">
          <el-select
            v-model="form.organization_id"
            placeholder="请选择所属机构（可选）"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="org in organizations"
              :key="org.organization_id"
              :label="org.name"
              :value="org.organization_id"
            />
          </el-select>
          <div class="form-tip">如不选择，用户将属于默认机构</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            创建用户
          </el-button>
          <el-button @click="handleCancel">
            取消
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { User, Message, Lock } from '@element-plus/icons-vue'

export default {
  name: 'AdminCreateUser',
  components: {
    User,
    Message,
    Lock
  },
  setup() {
    const router = useRouter()
    const adminStore = useAdminStore()
    const authStore = useAuthStore()

    const formRef = ref(null)
    const loading = ref(false)
    const organizations = ref([])

    const form = reactive({
      user_name: '',
      user_email: '',
      user_password: '',
      confirm_password: '',
      user_full_name: '',
      user_role: '',
      organization_id: ''
    })

    // 验证确认密码
    const validateConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'))
      } else if (value !== form.user_password) {
        callback(new Error('两次输入密码不一致'))
      } else {
        callback()
      }
    }

    const rules = {
      user_name: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' },
        { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
      ],
      user_email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
      ],
      user_password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
      ],
      confirm_password: [
        { required: true, validator: validateConfirmPassword, trigger: 'blur' }
      ],
      user_role: [
        { required: true, message: '请选择用户角色', trigger: 'change' }
      ]
    }

    // 检查当前用户是否可以创建管理员
    const canCreateAdmin = ref(false)

    const loadOrganizations = async () => {
      // 这里可以添加获取机构列表的逻辑
      // 暂时使用模拟数据
      organizations.value = [
        { organization_id: '1', name: '总部' },
        { organization_id: '2', name: '北京分部' },
        { organization_id: '3', name: '上海分部' }
      ]
    }

    const handleSubmit = async () => {
      try {
        // 表单验证
        const valid = await formRef.value.validate()
        if (!valid) return

        loading.value = true

        // 准备提交数据
        const submitData = {
          user_name: form.user_name,
          user_email: form.user_email,
          user_password: form.user_password,
          user_full_name: form.user_full_name || null,
          user_role: form.user_role,
          organization_id: form.organization_id || null
        }

        // 调用API创建用户
        await adminStore.createUser(submitData)

        ElMessage.success('用户创建成功')

        // 返回用户列表页面
        router.push('/admin/users')

      } catch (error) {
        console.error('创建用户失败:', error)
        ElMessage.error(error.response?.data?.message || '创建用户失败')
      } finally {
        loading.value = false
      }
    }

    const handleCancel = () => {
      router.back()
    }

    onMounted(() => {
      // 检查当前用户权限
      const currentUser = authStore.userInfo
      canCreateAdmin.value = currentUser.user_role === 'admin'

      // 加载机构列表
      loadOrganizations()
    })

    return {
      formRef,
      form,
      rules,
      loading,
      organizations,
      canCreateAdmin,
      handleSubmit,
      handleCancel
    }
  }
}
</script>

<style scoped>
.admin-create-user {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

:deep(.el-card__body) {
  padding: 24px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-select .el-input) {
  width: 100%;
}
</style>