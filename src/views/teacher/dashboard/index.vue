<template>
  <div class="dashboard-container">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="welcome-content">
        <div class="welcome-text">
          <h1>欢迎回来，{{ user.name }}！</h1>
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
          <div class="questions-list" v-if="!loading">
            <div v-if="recentQuestions.length === 0" class="empty-state">
              <p>暂无题目数据</p>
            </div>
            <div
              v-for="item in recentQuestions"
              :key="item.id"
              class="question-item"
              @click="viewQuestion(item)"
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
          <div v-else class="loading-state">
            <a-spin />
            <p>正在加载数据...</p>
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
import { useQuestionStore } from '@/stores/question'
import { useHomeworkStore } from '@/stores/homework'
import { useClassStore } from '@/stores/class'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'

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
      loading: false,
      stats: {
        totalQuestions: 0,
        totalHomework: 0,
        totalStudents: 0,
        aiCalls: 0,
        todayTasks: 0,
        activeStudents: 0
      },
      recentQuestions: []
    }
  },
  computed: {
    user() {
      const authStore = useAuthStore()
      return {
        name: authStore.userFullName || authStore.userName || '教师用户'
      }
    }
  },
  setup() {
    const questionStore = useQuestionStore()
    const homeworkStore = useHomeworkStore()
    const classStore = useClassStore()

    const { questions } = storeToRefs(questionStore)
    const { homeworks } = storeToRefs(homeworkStore)
    const { classes } = storeToRefs(classStore)

    return {
      questionStore,
      homeworkStore,
      classStore,
      questions,
      homeworks,
      classes
    }
  },
  async mounted() {
    await this.loadDashboardData()
  },
  methods: {
    async loadDashboardData() {
      this.loading = true
      try {
        // 并行加载各种数据
        await Promise.all([
          this.loadQuestions(),
          this.loadHomeworks(),
          this.loadClasses()
        ])

        // 更新统计数据
        this.updateStats()
      } catch (error) {
        console.error('加载仪表盘数据失败:', error)
      } finally {
        this.loading = false
      }
    },

    async loadQuestions() {
      try {
        await this.questionStore.fetchQuestions({ page: 1, size: 10 })
        // 设置最近题目
        this.recentQuestions = (this.questions || []).slice(0, 4).map(q => ({
          id: q.id,
          title: q.title,
          subject: q.subject,
          createTime: q.created_at ? new Date(q.created_at).toLocaleDateString() : '--',
          status: q.rewritten_answer ? '已改写' : '待改写'
        }))
      } catch (error) {
        console.error('加载题目数据失败:', error)
      }
    },

    async loadHomeworks() {
      try {
        await this.homeworkStore.fetchHomeworks({ page: 1, size: 50 })
      } catch (error) {
        console.error('加载作业数据失败:', error)
      }
    },

    async loadClasses() {
      try {
        await this.classStore.fetchClasses({ page: 1, size: 50 })
      } catch (error) {
        console.error('加载班级数据失败:', error)
      }
    },

    updateStats() {
      // 计算统计数据
      const questionsData = this.questions || []
      const homeworksData = this.homeworks || []
      const classesData = this.classes || []

      this.stats = {
        totalQuestions: questionsData.length,
        totalHomework: homeworksData.length,
        totalStudents: classesData.reduce((sum, cls) => sum + (cls.student_count || 0), 0),
        // AI调用次数暂时用改写过的题目数量估算
        aiCalls: questionsData.filter(q => q.rewritten_answer).length * 5,
        // 今日任务：未发布的作业数量
        todayTasks: homeworksData.filter(h => !h.is_published).length,
        // 活跃学生：估算值
        activeStudents: Math.floor(classesData.reduce((sum, cls) => sum + (cls.student_count || 0), 0) * 0.7)
      }
    },

    viewQuestion(question) {
      this.$router.push(`/teacher/question/${question.id}/detail`)
    },

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
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
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
  gap: 12px;
  overflow-y: auto;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.action-item:hover {
  transform: translateX(4px);
  border-color: #1890ff;
  background: #f6ffed;
}

.action-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: white;
  flex-shrink: 0;
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
  min-width: 0;
  overflow: hidden;
}

.action-title {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-desc {
  font-size: 12px;
  color: #8c8c8c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-arrow {
  color: #bfbfbf;
  transition: all 0.3s ease;
}

.action-item:hover .action-arrow {
  color: #1890ff;
  transform: translateX(4px);
}

/* 空状态和加载状态 */
.empty-state,
.loading-state {
  text-align: center;
  padding: 40px 20px;
  color: #8c8c8c;
}

.loading-state p {
  margin-top: 16px;
  margin-bottom: 0;
}
</style>