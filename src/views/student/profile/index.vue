<template>
  <div class="profile-container">
    <a-card :bordered="false" class="profile-card">
      <template #title>
        <div class="card-title">
          <UserOutlined />
          个人信息
        </div>
      </template>

      <a-form :model="form" :rules="rules" layout="vertical" @finish="handleSubmit">
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="用户名" name="username">
              <a-input v-model:value="form.username" disabled />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="邮箱" name="email">
              <a-input v-model:value="form.email" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="真实姓名" name="fullName">
              <a-input v-model:value="form.fullName" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="角色" name="role">
              <a-input v-model:value="form.role" disabled />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit" :loading="loading">保存修改</a-button>
            <a-button @click="handleCancel">取消</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
 </template>

<script>
import { UserOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { message } from 'ant-design-vue'
import { authApi } from '@/api/auth'

export default {
  name: 'StudentProfile',
  components: { UserOutlined },
  data() {
    return {
      form: { username: '', email: '', fullName: '', role: '' },
      rules: {
        email: [
          { required: true, message: '请输入邮箱' },
          { type: 'email', message: '请输入有效的邮箱地址' }
        ],
        fullName: [
          { required: true, message: '请输入真实姓名' }
        ]
      },
      loading: false
    }
  },
  mounted() {
    this.loadUserInfo()
  },
  methods: {
    loadUserInfo() {
      const authStore = useAuthStore()
      this.form = {
        username: authStore.userName || '',
        email: authStore.userEmail || '',
        fullName: authStore.userFullName || '',
        role: authStore.userRole === 'student' ? '学生' : (authStore.userRole || '用户')
      }
    },
    async handleSubmit() {
      this.loading = true
      try {
        const authStore = useAuthStore()
        const payload = { user_email: this.form.email, user_full_name: this.form.fullName }
        const updated = await authApi.updateProfile(payload)
        message.success('个人信息更新成功')
        // 更新本地用户信息
        authStore.user.user_full_name = updated?.user_full_name || this.form.fullName
        authStore.user.user_email = updated?.user_email || this.form.email
        localStorage.setItem('user', JSON.stringify(authStore.user))
      } catch (error) {
        message.error('更新失败：' + (error?.response?.data?.detail || error?.message || '未知错误'))
      } finally {
        this.loading = false
      }
    },
    handleCancel() {
      this.loadUserInfo()
    }
  }
}
</script>

<style scoped>
.profile-container { padding: 24px; }
.profile-card { max-width: 800px; margin: 0 auto; }
.card-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 500; }
.card-title .anticon { color: #3b82f6; }
</style>

