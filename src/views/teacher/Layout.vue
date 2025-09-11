<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible>
      <div class="logo">
        <div class="logo-container">
          <div class="logo-icon">
            <div class="icon-cube"></div>
          </div>
          <h3 v-if="!collapsed" class="logo-text">TeachAid</h3>
        </div>
      </div>
      <a-menu
        theme="dark"
        :default-selected-keys="[currentRoute]"
        mode="inline"
        @click="handleMenuClick"
      >
        <a-menu-item key="dashboard">
          <template #icon>
            <DashboardOutlined />
          </template>
          仪表板
        </a-menu-item>
        <a-menu-item key="question">
          <template #icon>
            <FileTextOutlined />
          </template>
          题目管理
        </a-menu-item>
        <a-menu-item key="homework">
          <template #icon>
            <BookOutlined />
          </template>
          作业管理
        </a-menu-item>
        <a-menu-item key="class">
          <template #icon>
            <TeamOutlined />
          </template>
          班级管理
        </a-menu-item>
        <a-menu-item key="prompt">
          <template #icon>
            <SettingOutlined />
          </template>
          提示词管理
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    
    <a-layout>
      <a-layout-header class="modern-header">
        <div class="header-content">
          <div class="header-left">
            <span class="page-title">{{ pageTitle }}</span>
            <div class="breadcrumb-container">
              <a-breadcrumb>
                <a-breadcrumb-item>教师工作台</a-breadcrumb-item>
                <a-breadcrumb-item>{{ pageTitle }}</a-breadcrumb-item>
              </a-breadcrumb>
            </div>
          </div>
          <div class="header-right">
            <a-space size="large">
              <a-tooltip title="通知">
                <a-badge :count="3" size="small">
                  <BellOutlined class="header-icon" />
                </a-badge>
              </a-tooltip>
              <a-tooltip title="设置">
                <SettingOutlined class="header-icon" />
              </a-tooltip>
              <a-dropdown>
                <a class="user-dropdown" @click.prevent>
                  <a-avatar size="small" style="background-color: #3b82f6;">T</a-avatar>
                  <span class="user-name">教师用户</span>
                  <DownOutlined />
                </a>
                <template #overlay>
                  <a-menu>
                    <a-menu-item key="profile">
                      <UserOutlined /> 个人信息
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item key="logout" @click="handleLogout">
                      <LogoutOutlined /> 退出登录
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </div>
        </div>
      </a-layout-header>
      
      <a-layout-content style="margin: 16px">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script>
import {
  DashboardOutlined,
  FileTextOutlined,
  BookOutlined,
  TeamOutlined,
  SettingOutlined,
  DownOutlined,
  BellOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons-vue'

export default {
  name: 'TeacherLayout',
  components: {
    DashboardOutlined,
    FileTextOutlined,
    BookOutlined,
    TeamOutlined,
    SettingOutlined,
    DownOutlined,
    BellOutlined,
    UserOutlined,
    LogoutOutlined
  },
  data() {
    return {
      collapsed: false
    }
  },
  computed: {
    currentRoute() {
      return this.$route.name?.replace('Teacher', '').toLowerCase() || 'dashboard'
    },
    pageTitle() {
      const titleMap = {
        dashboard: '仪表板',
        question: '题目管理',
        homework: '作业管理',
        class: '班级管理',
        prompt: '提示词管理'
      }
      return titleMap[this.currentRoute] || '仪表板'
    }
  },
  methods: {
    handleMenuClick({ key }) {
      this.$router.push(`/teacher/${key}`)
    },
    handleLogout() {
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.logo {
  height: 64px;
  margin: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.icon-cube {
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 3px;
  animation: cubeFloat 3s ease-in-out infinite;
}

@keyframes cubeFloat {
  0%, 100% { transform: translateY(0) rotateZ(0deg); }
  50% { transform: translateY(-3px) rotateZ(180deg); }
}

.logo-text {
  color: white;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  background: linear-gradient(135deg, #ffffff, #e2e8f0);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.modern-header {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 64px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.breadcrumb-container {
  opacity: 0.7;
}

.header-right {
  display: flex;
  align-items: center;
}

.header-icon {
  font-size: 16px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.3s ease;
}

.header-icon:hover {
  color: #3b82f6;
  transform: scale(1.1);
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  color: #1e293b;
  text-decoration: none;
}

.user-dropdown:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
}
</style>