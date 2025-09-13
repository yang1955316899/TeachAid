<template>
  <CommonLayout 
    user-type="student"
    :menu-items="menuItems"
    :user="user"
  />
</template>

<script>
import CommonLayout from '@/components/Layout/CommonLayout.vue'
import { useAuthStore } from '@/stores/auth'
import {
  DashboardOutlined,
  BookOutlined,
  ReadOutlined,
  BarChartOutlined,
  FileTextOutlined,
  UserOutlined
} from '@ant-design/icons-vue'

export default {
  name: 'StudentLayout',
  components: {
    CommonLayout,
    UserOutlined
  },
  data() {
    return {
      menuItems: [
        {
          key: 'dashboard',
          title: '学习仪表板',
          icon: DashboardOutlined
        },
        {
          key: 'homework',
          title: '我的作业',
          icon: BookOutlined
        },
        {
          key: 'study',
          title: '智能学习',
          icon: ReadOutlined
        },
        {
          key: 'progress',
          title: '学习进度',
          icon: BarChartOutlined
        },
        {
          key: 'notes',
          title: '我的笔记',
          icon: FileTextOutlined
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
        name: authStore.userFullName || authStore.userName || '学生用户',
        role: authStore.userRole === 'student' ? '学生' : '用户'
      }
    }
  }
}
</script>