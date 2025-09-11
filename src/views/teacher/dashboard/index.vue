<template>
  <div class="dashboard-container">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="welcome-content">
        <div class="welcome-text">
          <h1>欢迎回来，张老师！</h1>
          <p>今天又是充满活力的一天，让我们一起帮助学生们学习吧 🎯</p>
        </div>
        <div class="welcome-stats">
          <div class="stat-item">
            <div class="stat-number">{{ stats.todayTasks }}</div>
            <div class="stat-label">今日任务</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats.activeStudents }}</div>
            <div class="stat-label">活跃学生</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据统计卡片 -->
    <a-row :gutter="24" class="stats-row">
      <a-col :span="6">
        <div class="stat-card stat-card-1">
          <div class="stat-icon">
            <FileTextOutlined />
          </div>
          <div class="stat-info">
            <div class="stat-title">总题目数</div>
            <div class="stat-value">{{ stats.totalQuestions }}</div>
            <div class="stat-change">
              <ArrowUpOutlined /> +12 本周
            </div>
          </div>
        </div>
      </a-col>
      <a-col :span="6">
        <div class="stat-card stat-card-2">
          <div class="stat-icon">
            <BookOutlined />
          </div>
          <div class="stat-info">
            <div class="stat-title">总作业数</div>
            <div class="stat-value">{{ stats.totalHomework }}</div>
            <div class="stat-change">
              <ArrowUpOutlined /> +5 本周
            </div>
          </div>
        </div>
      </a-col>
      <a-col :span="6">
        <div class="stat-card stat-card-3">
          <div class="stat-icon">
            <TeamOutlined />
          </div>
          <div class="stat-info">
            <div class="stat-title">学生总数</div>
            <div class="stat-value">{{ stats.totalStudents }}</div>
            <div class="stat-change">
              <ArrowUpOutlined /> +8 本月
            </div>
          </div>
        </div>
      </a-col>
      <a-col :span="6">
        <div class="stat-card stat-card-4">
          <div class="stat-icon">
            <RobotOutlined />
          </div>
          <div class="stat-info">
            <div class="stat-title">AI调用次数</div>
            <div class="stat-value">{{ stats.aiCalls }}</div>
            <div class="stat-change">
              <ArrowUpOutlined /> +156 本周
            </div>
          </div>
        </div>
      </a-col>
    </a-row>

    <a-row :gutter="24" style="margin-top: 24px">
      <!-- 最近题目 -->
      <a-col :span="14">
        <div class="content-card">
          <div class="card-header">
            <h3>最近题目</h3>
            <a-button type="text" size="small">查看全部</a-button>
          </div>
          <div class="questions-list">
            <div
              v-for="item in recentQuestions"
              :key="item.id"
              class="question-item"
            >
              <div class="question-avatar">
                <span class="subject-tag" :class="getSubjectClass(item.subject)">
                  {{ item.subject.charAt(0) }}
                </span>
              </div>
              <div class="question-info">
                <div class="question-title">{{ item.title }}</div>
                <div class="question-meta">
                  <span class="question-subject">{{ item.subject }}</span>
                  <span class="question-time">{{ item.createTime }}</span>
                </div>
              </div>
              <div class="question-status">
                <a-tag :color="item.status === '已改写' ? 'success' : 'processing'">
                  {{ item.status }}
                </a-tag>
              </div>
            </div>
          </div>
        </div>
      </a-col>

      <!-- 快速操作 -->
      <a-col :span="10">
        <div class="content-card">
          <div class="card-header">
            <h3>快速操作</h3>
          </div>
          <div class="quick-actions">
            <div class="action-item" @click="$router.push('/teacher/question')">
              <div class="action-icon action-icon-1">
                <UploadOutlined />
              </div>
              <div class="action-info">
                <div class="action-title">上传新题目</div>
                <div class="action-desc">支持图片、PDF等多种格式</div>
              </div>
              <RightOutlined class="action-arrow" />
            </div>

            <div class="action-item" @click="$router.push('/teacher/homework')">
              <div class="action-icon action-icon-2">
                <EditOutlined />
              </div>
              <div class="action-info">
                <div class="action-title">创建作业</div>
                <div class="action-desc">选择题目组建作业</div>
              </div>
              <RightOutlined class="action-arrow" />
            </div>

            <div class="action-item" @click="$router.push('/teacher/prompt')">
              <div class="action-icon action-icon-3">
                <SettingOutlined />
              </div>
              <div class="action-info">
                <div class="action-title">管理提示词</div>
                <div class="action-desc">优化AI改写效果</div>
              </div>
              <RightOutlined class="action-arrow" />
            </div>

            <div class="action-item" @click="$router.push('/teacher/class')">
              <div class="action-icon action-icon-4">
                <UsergroupAddOutlined />
              </div>
              <div class="action-info">
                <div class="action-title">班级管理</div>
                <div class="action-desc">管理学生和班级信息</div>
              </div>
              <RightOutlined class="action-arrow" />
            </div>
          </div>
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script>
import {
  FileTextOutlined,
  BookOutlined,
  TeamOutlined,
  RobotOutlined,
  ArrowUpOutlined,
  UploadOutlined,
  EditOutlined,
  SettingOutlined,
  UsergroupAddOutlined,
  RightOutlined
} from '@ant-design/icons-vue'

export default {
  name: 'TeacherDashboard',
  components: {
    FileTextOutlined,
    BookOutlined,
    TeamOutlined,
    RobotOutlined,
    ArrowUpOutlined,
    UploadOutlined,
    EditOutlined,
    SettingOutlined,
    UsergroupAddOutlined,
    RightOutlined
  },
  data() {
    return {
      stats: {
        totalQuestions: 128,
        totalHomework: 45,
        totalStudents: 320,
        aiCalls: 1250,
        todayTasks: 8,
        activeStudents: 156
      },
      recentQuestions: [
        {
          id: 1,
          title: '二次函数综合应用题',
          subject: '数学',
          createTime: '2024-01-15',
          status: '已改写'
        },
        {
          id: 2,
          title: '英语阅读理解练习',
          subject: '英语',
          createTime: '2024-01-14',
          status: '待改写'
        },
        {
          id: 3,
          title: '物理力学计算题',
          subject: '物理',
          createTime: '2024-01-13',
          status: '已改写'
        },
        {
          id: 4,
          title: '化学方程式配平',
          subject: '化学',
          createTime: '2024-01-12',
          status: '已改写'
        }
      ]
    }
  },
  methods: {
    getSubjectClass(subject) {
      const classMap = {
        '数学': 'subject-math',
        '英语': 'subject-english',
        '物理': 'subject-physics',
        '化学': 'subject-chemistry'
      }
      return classMap[subject] || 'subject-default'
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  padding: 0;
}

/* 欢迎横幅 */
.welcome-banner {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 50%, #10b981 100%);
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 24px;
  color: white;
  position: relative;
  overflow: hidden;
  animation: gradientFlow 8s ease-in-out infinite;
}

@keyframes gradientFlow {
  0%, 100% {
    background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 50%, #10b981 100%);
  }
  33% {
    background: linear-gradient(135deg, #06b6d4 0%, #10b981 50%, #3b82f6 100%);
  }
  66% {
    background: linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #06b6d4 100%);
  }
}

.welcome-banner::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20px;
  width: 200px;
  height: 200px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 2;
}

.welcome-text h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
}

.welcome-text p {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.welcome-stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.8;
}

/* 统计卡片 */
.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-card-1 .stat-icon {
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
}

.stat-card-2 .stat-icon {
  background: linear-gradient(135deg, #10b981, #34d399);
}

.stat-card-3 .stat-icon {
  background: linear-gradient(135deg, #06b6d4, #0891b2);
}

.stat-card-4 .stat-icon {
  background: linear-gradient(135deg, #14b8a6, #0d9488);
}

.stat-info {
  flex: 1;
}

.stat-title {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #262626;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-change {
  font-size: 12px;
  color: #52c41a;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 内容卡片 */
.content-card {
  background: white;
  border-radius: 16px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  height: 400px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

/* 题目列表 */
.questions-list {
  flex: 1;
  padding: 16px 24px;
  overflow-y: auto;
}

.question-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
  transition: all 0.3s ease;
  cursor: pointer;
}

.question-item:hover {
  background: #fafafa;
  margin: 0 -16px;
  padding: 12px 16px;
  border-radius: 8px;
}

.question-item:last-child {
  border-bottom: none;
}

.question-avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.subject-tag {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.subject-math {
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
}

.subject-english {
  background: linear-gradient(135deg, #10b981, #34d399);
}

.subject-physics {
  background: linear-gradient(135deg, #06b6d4, #0891b2);
}

.subject-chemistry {
  background: linear-gradient(135deg, #14b8a6, #0d9488);
}

.subject-default {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.question-info {
  flex: 1;
}

.question-title {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 4px;
}

.question-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #8c8c8c;
}

/* 快速操作 */
.quick-actions {
  flex: 1;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-item:hover {
  transform: translateX(4px);
  border-color: #1890ff;
  background: #f6ffed;
}

.action-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
}

.action-icon-1 {
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
}

.action-icon-2 {
  background: linear-gradient(135deg, #10b981, #34d399);
}

.action-icon-3 {
  background: linear-gradient(135deg, #06b6d4, #0891b2);
}

.action-icon-4 {
  background: linear-gradient(135deg, #14b8a6, #0d9488);
}

.action-info {
  flex: 1;
}

.action-title {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 2px;
}

.action-desc {
  font-size: 12px;
  color: #8c8c8c;
}

.action-arrow {
  color: #bfbfbf;
  transition: all 0.3s ease;
}

.action-item:hover .action-arrow {
  color: #1890ff;
  transform: translateX(4px);
}
</style>