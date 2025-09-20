<template>
  <div class="admin-layout">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="250px" class="admin-sidebar">
        <div class="sidebar-header">
          <h3>管理员中心</h3>
        </div>
        <el-menu
          :default-active="activeMenu"
          :router="true"
          class="sidebar-menu"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/admin/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>

          <el-sub-menu index="users">
            <template #title>
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </template>
            <el-menu-item index="/admin/users">用户列表</el-menu-item>
            <el-menu-item index="/admin/users/create">创建用户</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="classes">
            <template #title>
              <el-icon><School /></el-icon>
              <span>班级管理</span>
            </template>
            <el-menu-item index="/admin/classes">班级列表</el-menu-item>
            <el-menu-item index="/admin/classes/create">创建班级</el-menu-item>
            <el-menu-item index="/admin/teaching-assignments">授课安排</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="content">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>内容管理</span>
            </template>
            <el-menu-item index="/admin/homeworks">作业管理</el-menu-item>
            <el-menu-item index="/admin/questions">题目管理</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="system">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </template>
            <el-menu-item index="/admin/settings">系统设置</el-menu-item>
            <el-menu-item index="/admin/permissions">权限管理</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="analytics">
            <template #title>
              <el-icon><DataAnalysis /></el-icon>
              <span>数据分析</span>
            </template>
            <el-menu-item index="/admin/analytics/overview">数据概览</el-menu-item>
            <el-menu-item index="/admin/analytics/users">用户分析</el-menu-item>
            <el-menu-item index="/admin/analytics/content">内容分析</el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/admin/profile">
            <el-icon><Avatar /></el-icon>
            <span>个人信息</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航 -->
        <el-header class="admin-header">
          <div class="header-left">
            <breadcrumb />
          </div>
          <div class="header-right">
            <el-dropdown @command="handleCommand">
              <span class="el-dropdown-link">
                <el-avatar :size="32" :src="userInfo.avatar" />
                <span class="username">{{ userInfo.user_full_name || userInfo.user_name }}</span>
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <!-- 主内容 -->
        <el-main class="admin-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Breadcrumb from './components/Breadcrumb.vue'
import {
  Odometer,
  User,
  School,
  Document,
  Setting,
  DataAnalysis,
  Avatar,
  ArrowDown
} from '@element-plus/icons-vue'

export default {
  name: 'AdminLayout',
  components: {
    Breadcrumb,
    Odometer,
    User,
    School,
    Document,
    Setting,
    DataAnalysis,
    Avatar,
    ArrowDown
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const authStore = useAuthStore()

    const activeMenu = computed(() => {
      return route.path
    })

    const userInfo = computed(() => {
      return authStore.userInfo
    })

    const handleCommand = (command) => {
      switch (command) {
        case 'profile':
          router.push('/admin/profile')
          break
        case 'logout':
          authStore.logout()
          router.push('/login')
          break
      }
    }

    return {
      activeMenu,
      userInfo,
      handleCommand
    }
  }
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  background-color: #f0f2f5;
}

.admin-sidebar {
  background-color: #304156;
  overflow: hidden;
}

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2c3e50;
  color: #fff;
  border-bottom: 1px solid #34495e;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.sidebar-menu {
  border-right: none;
  min-height: calc(100vh - 60px);
}

.admin-header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
}

.header-left {
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
}

.el-dropdown-link {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #606266;
}

.username {
  margin: 0 8px;
  font-size: 14px;
}

.admin-main {
  background-color: #f0f2f5;
  padding: 20px;
  min-height: calc(100vh - 60px);
}

:deep(.el-menu-item), :deep(.el-sub-menu__title) {
  height: 50px;
  line-height: 50px;
}

:deep(.el-menu-item) {
  border-radius: 0;
}

:deep(.el-menu-item.is-active) {
  background-color: #409EFF !important;
}

:deep(.el-sub-menu .el-menu-item) {
  background-color: #263445 !important;
  min-width: 0;
}

:deep(.el-sub-menu .el-menu-item:hover) {
  background-color: #48576a !important;
}

:deep(.el-sub-menu .el-menu-item.is-active) {
  background-color: #409EFF !important;
}
</style>

