<template>
  <div class="analytics-overview">
    <div class="header">
      <h2>数据概览</h2>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        @change="handleDateChange"
      />
    </div>

    <!-- 概览卡片 -->
    <el-row :gutter="20" class="overview-cards">
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-content">
            <div class="card-icon user-icon">
              <el-icon><User /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-title">总用户数</div>
              <div class="card-value">{{ overviewData.totalUsers }}</div>
              <div class="card-trend" :class="{ positive: overviewData.userGrowth > 0 }">
                <el-icon><TrendCharts /></el-icon>
                {{ overviewData.userGrowth > 0 ? '+' : '' }}{{ overviewData.userGrowth }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-content">
            <div class="card-icon question-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-title">题目总数</div>
              <div class="card-value">{{ overviewData.totalQuestions }}</div>
              <div class="card-trend" :class="{ positive: overviewData.questionGrowth > 0 }">
                <el-icon><TrendCharts /></el-icon>
                {{ overviewData.questionGrowth > 0 ? '+' : '' }}{{ overviewData.questionGrowth }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-content">
            <div class="card-icon homework-icon">
              <el-icon><Notebook /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-title">作业总数</div>
              <div class="card-value">{{ overviewData.totalHomeworks }}</div>
              <div class="card-trend" :class="{ positive: overviewData.homeworkGrowth > 0 }">
                <el-icon><TrendCharts /></el-icon>
                {{ overviewData.homeworkGrowth > 0 ? '+' : '' }}{{ overviewData.homeworkGrowth }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-content">
            <div class="card-icon chat-icon">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-title">AI对话数</div>
              <div class="card-value">{{ overviewData.totalChats }}</div>
              <div class="card-trend" :class="{ positive: overviewData.chatGrowth > 0 }">
                <el-icon><TrendCharts /></el-icon>
                {{ overviewData.chatGrowth > 0 ? '+' : '' }}{{ overviewData.chatGrowth }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-section">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>用户增长趋势</span>
            </div>
          </template>
          <div ref="userGrowthChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>内容创建趋势</span>
            </div>
          </template>
          <div ref="contentGrowthChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-section">
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>用户角色分布</span>
            </div>
          </template>
          <div ref="userRoleChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>学科分布</span>
            </div>
          </template>
          <div ref="subjectChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>AI模型使用情况</span>
            </div>
          </template>
          <div ref="aiModelChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细统计表格 -->
    <el-card class="detail-table">
      <template #header>
        <div class="card-header">
          <span>详细统计</span>
        </div>
      </template>
      <el-table :data="detailStats" stripe>
        <el-table-column prop="metric" label="指标" width="200" />
        <el-table-column prop="today" label="今日" width="100" />
        <el-table-column prop="yesterday" label="昨日" width="100" />
        <el-table-column prop="thisWeek" label="本周" width="100" />
        <el-table-column prop="lastWeek" label="上周" width="100" />
        <el-table-column prop="thisMonth" label="本月" width="100" />
        <el-table-column prop="lastMonth" label="上月" width="100" />
        <el-table-column prop="growth" label="增长率" width="120">
          <template #default="{ row }">
            <span :class="{ 'positive-growth': row.growth > 0, 'negative-growth': row.growth < 0 }">
              {{ row.growth > 0 ? '+' : '' }}{{ row.growth }}%
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { User, Document, Notebook, ChatDotRound, TrendCharts } from '@element-plus/icons-vue'

const dateRange = ref([])

const overviewData = reactive({
  totalUsers: 1250,
  userGrowth: 12.5,
  totalQuestions: 3420,
  questionGrowth: 8.3,
  totalHomeworks: 856,
  homeworkGrowth: 15.2,
  totalChats: 12580,
  chatGrowth: 22.1
})

const detailStats = ref([
  {
    metric: '新增用户',
    today: 25,
    yesterday: 18,
    thisWeek: 165,
    lastWeek: 142,
    thisMonth: 650,
    lastMonth: 580,
    growth: 12.1
  },
  {
    metric: '新增题目',
    today: 12,
    yesterday: 15,
    thisWeek: 85,
    lastWeek: 78,
    thisMonth: 320,
    lastMonth: 295,
    growth: 8.5
  },
  {
    metric: '新增作业',
    today: 8,
    yesterday: 6,
    thisWeek: 45,
    lastWeek: 39,
    thisMonth: 180,
    lastMonth: 156,
    growth: 15.4
  },
  {
    metric: 'AI对话次数',
    today: 420,
    yesterday: 380,
    thisWeek: 2800,
    lastWeek: 2300,
    thisMonth: 11500,
    lastMonth: 9200,
    growth: 25.0
  }
])

// 图表容器引用
const userGrowthChart = ref()
const contentGrowthChart = ref()
const userRoleChart = ref()
const subjectChart = ref()
const aiModelChart = ref()

const handleDateChange = (dates) => {
  console.log('Date range changed:', dates)
  // TODO: 根据日期范围更新数据
}

const initCharts = async () => {
  await nextTick()

  // 这里应该使用实际的图表库（如 ECharts）来初始化图表
  // 由于没有安装图表库，这里只是模拟

  if (userGrowthChart.value) {
    userGrowthChart.value.innerHTML = '<div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #999;">用户增长趋势图 (需要ECharts)</div>'
  }

  if (contentGrowthChart.value) {
    contentGrowthChart.value.innerHTML = '<div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #999;">内容创建趋势图 (需要ECharts)</div>'
  }

  if (userRoleChart.value) {
    userRoleChart.value.innerHTML = '<div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #999;">用户角色分布图 (需要ECharts)</div>'
  }

  if (subjectChart.value) {
    subjectChart.value.innerHTML = '<div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #999;">学科分布图 (需要ECharts)</div>'
  }

  if (aiModelChart.value) {
    aiModelChart.value.innerHTML = '<div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #999;">AI模型使用图 (需要ECharts)</div>'
  }
}

onMounted(() => {
  // 设置默认日期范围为最近30天
  const end = new Date()
  const start = new Date()
  start.setTime(start.getTime() - 30 * 24 * 60 * 60 * 1000)
  dateRange.value = [start, end]

  initCharts()
})
</script>

<style scoped>
.analytics-overview {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.overview-cards {
  margin-bottom: 20px;
}

.overview-card {
  height: 120px;
}

.card-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: white;
}

.user-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.question-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.homework-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.chat-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.card-info {
  flex: 1;
}

.card-title {
  font-size: 14px;
  color: #999;
  margin-bottom: 5px;
}

.card-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.card-trend {
  font-size: 12px;
  color: #999;
  display: flex;
  align-items: center;
}

.card-trend.positive {
  color: #67c23a;
}

.card-trend .el-icon {
  margin-right: 3px;
}

.charts-section {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
}

.detail-table {
  margin-top: 20px;
}

.positive-growth {
  color: #67c23a;
  font-weight: bold;
}

.negative-growth {
  color: #f56c6c;
  font-weight: bold;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>