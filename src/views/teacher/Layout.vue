<template>
  <CommonLayout 
    user-type="teacher"
    :menu-items="menuItems"
    :user="user"
  />
</template>

<script>
import CommonLayout from '@/components/Layout/CommonLayout.vue'
import { useAuthStore } from '@/stores/auth'
import {
  DashboardOutlined,
  FileTextOutlined,
  BookOutlined,
  TeamOutlined,
  LinkOutlined,
  SettingOutlined,
  UserOutlined
} from '@ant-design/icons-vue'

export default {
  name: 'TeacherLayout',
  components: {
    CommonLayout
  },
  data() {
    return {
      menuItems: [
        {
          key: 'dashboard',
          title: '仪表板',
          icon: DashboardOutlined
        },
        {
          key: 'question',
          title: '题目管理',
          icon: FileTextOutlined
        },
        {
          key: 'homework',
          title: '作业管理',
          icon: BookOutlined
        },
        {
          key: 'class',
          title: '班级管理',
          icon: TeamOutlined
        },
        {
          key: 'teaching',
          title: '授课关系管理',
          icon: LinkOutlined
        },
        {
          key: 'prompt',
          title: '提示词管理',
          icon: SettingOutlined
        },
        {
          key: 'profile',
          title: '个人信息',
          icon: UserOutlined
        }
      ]
    }
  },
  computed: {
    user() {
      const authStore = useAuthStore()
      return {
        name: authStore.userFullName || authStore.userName || '教师用户',
        role: authStore.userRole === 'teacher' ? '教师' : '用户'
      }
    }
  }
}
</script>