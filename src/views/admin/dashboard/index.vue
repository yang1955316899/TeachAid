<template>
  <div class="admin-dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>管理员仪表盘</h1>
      <p>系统运行状态总览</p>
    </div>

    <!-- 数据统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon users">
              <el-icon><User /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ systemStats.total_users }}</div>
              <div class="stats-label">总用户数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon teachers">
              <el-icon><Avatar /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ systemStats.total_teachers }}</div>
              <div class="stats-label">教师数量</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon students">
              <el-icon><UserFilled /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ systemStats.total_students }}</div>
              <div class="stats-label">学生数量</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon classes">
              <el-icon><School /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ systemStats.total_classes }}</div>
              <div class="stats-label">班级数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细统计 -->
    <el-row :gutter="20" class="detail-row">
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon questions">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ systemStats.total_questions }}</div>
              <div class="stats-label">题目总数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon homeworks">
              <el-icon><Files /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ systemStats.total_homeworks }}</div>
              <div class="stats-label">作业总数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon active-today">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ systemStats.active_users_today }}</div>
              <div class="stats-label">今日活跃</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon active-week">
              <el-icon><DataLine /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ systemStats.active_users_week }}</div>
              <div class="stats-label">本周活跃</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近登录和快捷操作 -->
    <el-row :gutter="20" class="bottom-row">
      <!-- 最近登录 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近登录</span>
              <el-button type="text" @click="$router.push('/admin/users')">查看更多</el-button>
            </div>
          </template>
          <div class="recent-logins">
            <div
              v-for="login in systemStats.recent_logins.slice(0, 5)"
              :key="login.username"
              class="login-item"
            >
              <div class="login-user">
                <el-avatar :size="32">{{ login.username.charAt(0).toUpperCase() }}</el-avatar>
                <div class="login-info">
                  <div class="username">{{ login.username }}</div>
                  <div class="login-time">{{ formatTime(login.logged_in_at) }}</div>
                </div>
              </div>
              <div class="login-ip">{{ login.ip_address }}</div>
            </div>
            <div v-if="systemStats.recent_logins.length === 0" class="no-data">
              暂无登录记录
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 快捷操作 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快捷操作</span>
            </div>
          </template>
          <div class="quick-actions">
            <el-row :gutter="15">
              <el-col :span="12">
                <el-button
                  type="primary"
                  size="large"
                  class="action-btn"
                  @click="$router.push('/admin/users/create')"
                >
                  <el-icon><Plus /></el-icon>
                  创建用户
                </el-button>
              </el-col>
              <el-col :span="12">
                <el-button
                  type="success"
                  size="large"
                  class="action-btn"
                  @click="$router.push('/admin/classes/create')"
                >
                  <el-icon><Plus /></el-icon>
                  创建班级
                </el-button>
              </el-col>
              <el-col :span="12">
                <el-button
                  type="warning"
                  size="large"
                  class="action-btn"
                  @click="$router.push('/admin/settings')"
                >
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-button>
              </el-col>
              <el-col :span="12">
                <el-button
                  type="info"
                  size="large"
                  class="action-btn"
                  @click="$router.push('/admin/analytics/overview')"
                >
                  <el-icon><DataAnalysis /></el-icon>
                  数据分析
                </el-button>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'
import {
  User,
  Avatar,
  UserFilled,
  School,
  Document,
  Files,
  Calendar,
  DataLine,
  Plus,
  Setting,
  DataAnalysis
} from '@element-plus/icons-vue'

export default {
  name: 'AdminDashboard',
  components: {
    User,
    Avatar,
    UserFilled,
    School,
    Document,
    Files,
    Calendar,
    DataLine,
    Plus,
    Setting,
    DataAnalysis
  },
  setup() {
    const adminStore = useAdminStore()
    const loading = ref(false)

    const systemStats = ref({
      total_users: 0,
      total_teachers: 0,
      total_students: 0,
      total_admins: 0,
      total_classes: 0,
      total_questions: 0,
      total_homeworks: 0,
      active_users_today: 0,
      active_users_week: 0,
      recent_logins: []
    })

    const loadData = async () => {
      loading.value = true
      try {
        await adminStore.fetchSystemStats()
        systemStats.value = adminStore.systemStats
      } catch (error) {
        console.error('加载仪表盘数据失败:', error)
        ElMessage.error('加载数据失败')
      } finally {
        loading.value = false
      }
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return '--'
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date

      if (diff < 60000) { // 1分钟内
        return '刚刚'
      } else if (diff < 3600000) { // 1小时内
        return `${Math.floor(diff / 60000)}分钟前`
      } else if (diff < 86400000) { // 24小时内
        return `${Math.floor(diff / 3600000)}小时前`
      } else {
        return date.toLocaleDateString()
      }
    }

    onMounted(() => {
      loadData()
    })

    return {
      systemStats,
      loading,
      formatTime,
      loadData
    }
  }
}
</script>

<style scoped>
.admin-dashboard {
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

.stats-row,
.detail-row {
  margin-bottom: 20px;
}

.bottom-row {
  margin-top: 20px;
}

.stats-card {
  height: 100px;
}

.stats-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stats-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.stats-icon.users {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stats-icon.teachers {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stats-icon.students {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stats-icon.classes {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stats-icon.questions {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stats-icon.homeworks {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
}

.stats-icon.active-today {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
}

.stats-icon.active-week {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
}

.stats-info {
  flex: 1;
}

.stats-number {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.stats-label {
  font-size: 14px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recent-logins {
  min-height: 200px;
}

.login-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.login-item:last-child {
  border-bottom: none;
}

.login-user {
  display: flex;
  align-items: center;
  flex: 1;
}

.login-info {
  margin-left: 12px;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 2px;
}

.login-time {
  font-size: 12px;
  color: #909399;
}

.login-ip {
  font-size: 12px;
  color: #909399;
}

.no-data {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.quick-actions {
  padding: 20px 0;
}

.action-btn {
  width: 100%;
  height: 60px;
  margin-bottom: 15px;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn .el-icon {
  margin-right: 8px;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}
</style>

