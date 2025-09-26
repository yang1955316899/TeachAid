<template>
  <CommonLayout
    user-type="admin"
    :menu-items="menuItems"
    :user="user"
  />
</template>

<script>
import CommonLayout from '@/components/Layout/CommonLayout.vue'
import { useAuthStore } from '@/stores/auth'
import {
  DashboardOutlined,
  UserOutlined,
  TeamOutlined,
  FileTextOutlined,
  SettingOutlined,
  BarChartOutlined,
  ContactsOutlined
} from '@ant-design/icons-vue'

export default {
  name: 'AdminLayout',
  components: {
    CommonLayout
  },
  data() {
    return {
      menuItems: [
        {
          key: 'dashboard',
          title: '仪表盘',
          icon: DashboardOutlined
        },
        {
          key: 'users',
          title: '用户管理',
          icon: UserOutlined
        },
        {
          key: 'classes',
          title: '班级管理',
          icon: TeamOutlined
        },
        {
          key: 'homeworks',
          title: '作业管理',
          icon: FileTextOutlined
        },
        {
          key: 'questions',
          title: '题目管理',
          icon: FileTextOutlined
        },
        {
          key: 'analytics',
          title: '数据分析',
          icon: BarChartOutlined,
          children: [
            {
              key: 'analytics/overview',
              title: '数据概览'
            },
            {
              key: 'analytics/users',
              title: '用户分析'
            },
            {
              key: 'analytics/content',
              title: '内容分析'
            }
          ]
        },
        {
          key: 'settings',
          title: '系统设置',
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
        name: authStore.userFullName || authStore.userName || '管理员',
        role: authStore.userRole === 'admin' ? '管理员' : '用户'
      }
    }
  }
}
</script>


