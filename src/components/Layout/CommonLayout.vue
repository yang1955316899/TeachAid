<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible :width="collapsed ? 80 : 240" class="sidebar">
      <div class="logo-container">
        <div class="logo">
          <div class="logo-icon">
            <BookOutlined />
          </div>
          <div v-if="!collapsed" class="logo-text">
            <h3>TeachAid</h3>
            <p>AI辅助教学平台</p>
          </div>
        </div>
      </div>
      <div class="menu-container">
        <a-menu
          v-model:selectedKeys="selectedKeys"
          theme="dark"
          mode="inline"
          @click="handleMenuClick"
          class="custom-menu"
        >
          <a-menu-item v-for="item in menuItems" :key="item.key">
            <template #icon>
              <component :is="item.icon" />
            </template>
            {{ item.title }}
          </a-menu-item>
        </a-menu>
      </div>
    </a-layout-sider>
    
    <a-layout>
      <a-layout-header style="background: #fff; padding: 0">
        <div class="header-content">
          <span class="page-title">{{ currentTitle }}</span>
          <div class="user-profile">
            <a-dropdown>
              <div class="user-dropdown-trigger">
                <div class="user-avatar">
                  <UserOutlined />
                </div>
                <div v-if="!collapsed" class="user-info">
                  <div class="user-name">{{ user.name }}</div>
                  <div class="user-role">{{ user.role }}</div>
                </div>
                <DownOutlined v-if="!collapsed" class="dropdown-arrow" />
              </div>
              <template #overlay>
                <a-menu @click="handleMenuClick">
                  <a-menu-item key="profile">
                    <UserOutlined />
                    个人信息
                  </a-menu-item>
                  <a-menu-item key="settings">
                    <SettingOutlined />
                    账户设置
                  </a-menu-item>
                  <a-menu-divider />
                  <a-menu-item key="logout" @click="handleLogout">
                    <LogoutOutlined />
                    退出登录
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
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
  BookOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  DownOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'CommonLayout',
  components: {
    BookOutlined,
    UserOutlined,
    SettingOutlined,
    LogoutOutlined,
    DownOutlined
  },
  props: {
    userType: {
      type: String,
      required: true,
      validator: (value) => ['student', 'teacher'].includes(value)
    },
    menuItems: {
      type: Array,
      required: true
    },
    user: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      collapsed: false,
      selectedKeys: []
    }
  },
  computed: {
    currentRoute() {
      return this.$route.name?.replace(this.userType.charAt(0).toUpperCase() + this.userType.slice(1), '').toLowerCase() || this.menuItems[0].key
    },
    currentTitle() {
      const item = this.menuItems.find(item => item.key === this.currentRoute)
      return item ? item.title : this.menuItems[0].title
    }
  },
  mounted() {
    // 初始化选中的菜单项
    this.selectedKeys = [this.currentRoute]
  },
  methods: {
    handleMenuClick({ key }) {
      this.selectedKeys = [key]
      this.$router.push(`/${this.userType}/${key}`)
    },
    handleDropdownClick({ key }) {
      if (key === 'profile') {
        this.$router.push(`/${this.userType}/profile`)
      } else if (key === 'settings') {
        // 账户设置功能待实现
        console.log('账户设置功能待实现')
      }
    },
    async handleLogout() {
      try {
        const authStore = useAuthStore()
        await authStore.logout()
      } catch (error) {
        console.error('退出登录失败:', error)
        // 即使API调用失败，也跳转到登录页
        this.$router.push('/login')
      }
    }
  }
}
</script>

<style scoped>
/* 侧边栏样式 */
.sidebar {
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  overflow: hidden !important;
}

/* Logo容器 */
.logo-container {
  padding: 20px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
  width: 100%;
  justify-content: center;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.logo-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  text-align: left;
  overflow: hidden;
}

.logo-text h3 {
  color: white;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
}

.logo-text p {
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
  font-size: 10px;
  font-weight: 400;
  line-height: 1;
  white-space: nowrap;
}

/* 菜单容器 */
.menu-container {
  padding: 16px 8px;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
}

/* 自定义菜单样式 */
.custom-menu {
  background: transparent !important;
  border: none !important;
}

.custom-menu :deep(.ant-menu-item) {
  margin: 2px 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  height: 44px;
  display: flex;
  align-items: center;
}

.custom-menu :deep(.ant-menu-item:hover) {
  background: rgba(59, 130, 246, 0.1) !important;
  transform: translateX(2px);
}

.custom-menu :deep(.ant-menu-item-selected) {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%) !important;
  border-left: 3px solid #3b82f6;
  transform: translateX(2px);
}

.custom-menu :deep(.ant-menu-item::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.1), transparent);
  transition: left 0.4s ease;
}

.custom-menu :deep(.ant-menu-item:hover::before) {
  left: 100%;
}

.custom-menu :deep(.ant-menu-item .anticon) {
  font-size: 14px;
  margin-right: 8px;
  transition: transform 0.3s ease;
}

.custom-menu :deep(.ant-menu-item:hover .anticon) {
  transform: scale(1.05);
}

.custom-menu :deep(.ant-menu-item-selected .anticon) {
  color: #3b82f6;
}

/* 折叠状态样式 */
.sidebar:has(.ant-layout-sider-collapsed) .logo-container {
  padding: 20px 8px;
}

.sidebar:has(.ant-layout-sider-collapsed) .logo-icon {
  width: 32px;
  height: 32px;
  font-size: 14px;
}

.sidebar:has(.ant-layout-sider-collapsed) .custom-menu :deep(.ant-menu-item) {
  justify-content: center;
  margin: 4px 8px;
}

.sidebar:has(.ant-layout-sider-collapsed) .custom-menu :deep(.ant-menu-item .anticon) {
  margin-right: 0;
}

.sidebar:has(.ant-layout-sider-collapsed) .menu-container {
  padding: 16px 4px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 64px;
  min-width: 0;
}

.page-title {
  font-size: 18px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 用户头像和下拉菜单样式 */
.user-profile {
  position: relative;
  flex-shrink: 0;
}

.user-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 12px;
  border-radius: 20px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: fit-content;
}

.user-dropdown-trigger:hover {
  background: rgba(59, 130, 246, 0.15);
  border-color: #3b82f6;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  font-weight: 500;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1px;
  min-width: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: #262626;
  line-height: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px;
}

.user-role {
  font-size: 11px;
  color: #64748b;
  font-weight: 400;
  line-height: 1;
  white-space: nowrap;
}

.dropdown-arrow {
  color: #64748b;
  font-size: 10px;
  transition: transform 0.3s ease;
  margin-left: 4px;
}

.user-dropdown-trigger:hover .dropdown-arrow {
  transform: rotate(180deg);
  color: #3b82f6;
}
</style>