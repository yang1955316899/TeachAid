<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible>
      <div class="logo">
        <h3 v-if="!collapsed">TeachAid</h3>
        <h3 v-else>TA</h3>
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
          学习仪表板
        </a-menu-item>
        <a-menu-item key="homework">
          <template #icon>
            <BookOutlined />
          </template>
          我的作业
        </a-menu-item>
        <a-menu-item key="study">
          <template #icon>
            <ReadOutlined />
          </template>
          智能学习
        </a-menu-item>
        <a-menu-item key="progress">
          <template #icon>
            <BarChartOutlined />
          </template>
          学习进度
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    
    <a-layout>
      <a-layout-header style="background: #fff; padding: 0">
        <div class="header-content">
          <span class="page-title">{{ pageTitle }}</span>
          <a-dropdown>
            <a class="ant-dropdown-link" @click.prevent>
              学生用户 <DownOutlined />
            </a>
            <template #overlay>
              <a-menu>
                <a-menu-item key="logout" @click="handleLogout">
                  退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
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
  BookOutlined,
  ReadOutlined,
  BarChartOutlined,
  DownOutlined
} from '@ant-design/icons-vue'

export default {
  name: 'StudentLayout',
  components: {
    DashboardOutlined,
    BookOutlined,
    ReadOutlined,
    BarChartOutlined,
    DownOutlined
  },
  data() {
    return {
      collapsed: false
    }
  },
  computed: {
    currentRoute() {
      return this.$route.name?.replace('Student', '').toLowerCase() || 'dashboard'
    },
    pageTitle() {
      const titleMap = {
        dashboard: '学习仪表板',
        homework: '我的作业',
        study: '智能学习',
        progress: '学习进度'
      }
      return titleMap[this.currentRoute] || '学习仪表板'
    }
  },
  methods: {
    handleMenuClick({ key }) {
      this.$router.push(`/student/${key}`)
    },
    handleLogout() {
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.logo {
  height: 32px;
  margin: 16px;
  color: white;
  text-align: center;
}

.logo h3 {
  color: white;
  margin: 0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 64px;
}

.page-title {
  font-size: 18px;
  font-weight: 500;
}
</style>