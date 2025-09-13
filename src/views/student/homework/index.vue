<template>
  <div>
    <a-card title="我的作业" style="margin-bottom: 16px">
      <!-- 统计信息 -->
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="6">
          <a-card>
            <a-statistic title="总作业数" :value="statistics.total" />
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic 
              title="已完成" 
              :value="statistics.completed" 
              value-style="{ color: '#3f8600' }"
            />
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic 
              title="进行中" 
              :value="statistics.inProgress" 
              value-style="{ color: '#cf1322' }"
            />
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic 
              title="平均完成率" 
              :value="statistics.averageCompletionRate" 
              suffix="%"
              :precision="1"
            />
          </a-card>
        </a-col>
      </a-row>

      <!-- 筛选标签 -->
      <a-space style="margin-bottom: 16px">
        <a-checkable-tag
          v-model:checked="filters.all"
          @change="handleFilterChange('all')"
        >
          全部
        </a-checkable-tag>
        <a-checkable-tag
          v-model:checked="filters.pending"
          @change="handleFilterChange('pending')"
        >
          待完成
        </a-checkable-tag>
        <a-checkable-tag
          v-model:checked="filters.inProgress"
          @change="handleFilterChange('inProgress')"
        >
          进行中
        </a-checkable-tag>
        <a-checkable-tag
          v-model:checked="filters.completed"
          @change="handleFilterChange('completed')"
        >
          已完成
        </a-checkable-tag>
        <a-checkable-tag
          v-model:checked="filters.overdue"
          @change="handleFilterChange('overdue')"
        >
          已逾期
        </a-checkable-tag>
      </a-space>
      
      <a-table
        :columns="columns"
        :data-source="filteredHomeworks"
        :loading="loading"
        :pagination="{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: handlePaginationChange,
          onShowSizeChange: handlePaginationChange
        }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'dueDate'">
            <span :class="{ 'text-red-500': isOverdue(record.due_date) }">
              {{ formatDate(record.due_date) }}
              <a-tag v-if="isOverdue(record.due_date)" color="red" size="small">已逾期</a-tag>
            </span>
          </template>
          <template v-if="column.key === 'progress'">
            <a-progress 
              :percent="record.progress || 0" 
              :show-info="true"
              size="small"
              :status="getProgressStatus(record.status)"
            />
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button
                v-if="record.status === 'pending' || record.status === 'in_progress'"
                size="small"
                type="primary"
                @click="startStudy(record)"
              >
                继续学习
              </a-button>
              <a-button
                v-else-if="record.status === 'completed'"
                size="small"
                @click="viewResult(record)"
              >
                查看结果
              </a-button>
              <a-button
                size="small"
                @click="viewDetail(record)"
              >
                查看详情
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script>
import { useStudentHomeworkStore } from '@/stores/studentHomework'
import { storeToRefs } from 'pinia'

export default {
  name: 'StudentHomework',
  data() {
    return {
      filters: {
        all: true,
        pending: false,
        inProgress: false,
        completed: false,
        overdue: false
      },
      columns: [
        {
          title: '作业标题',
          dataIndex: 'title',
          key: 'title'
        },
        {
          title: '班级',
          dataIndex: 'class_name',
          key: 'className'
        },
        {
          title: '学科',
          dataIndex: 'subject',
          key: 'subject'
        },
        {
          title: '题目数量',
          dataIndex: 'question_count',
          key: 'questionCount'
        },
        {
          title: '截止时间',
          dataIndex: 'due_date',
          key: 'dueDate'
        },
        {
          title: '进度',
          dataIndex: 'progress',
          key: 'progress'
        },
        {
          title: '状态',
          dataIndex: 'status',
          key: 'status'
        },
        {
          title: '操作',
          key: 'action'
        }
      ],
      statistics: {
        total: 0,
        completed: 0,
        inProgress: 0,
        averageCompletionRate: 0
      }
    }
  },
  computed: {
    homeworkStore() {
      return useStudentHomeworkStore()
    },
    filteredHomeworks() {
      let filtered = this.homeworks
      
      if (!this.filters.all) {
        const activeFilters = Object.keys(this.filters).filter(key => this.filters[key] && key !== 'all')
        if (activeFilters.length > 0) {
          filtered = filtered.filter(homework => {
            if (this.filters.pending && homework.status === 'pending') return true
            if (this.filters.inProgress && homework.status === 'in_progress') return true
            if (this.filters.completed && homework.status === 'completed') return true
            if (this.filters.overdue && this.isOverdue(homework.due_date) && homework.status !== 'completed') return true
            return false
          })
        }
      }
      
      return filtered
    }
  },
  setup() {
    const homeworkStore = useStudentHomeworkStore()
    const { homeworks, loading, pagination } = storeToRefs(homeworkStore)
    
    return {
      homeworks,
      loading,
      pagination
    }
  },
  mounted() {
    this.loadHomeworks()
  },
  methods: {
    async loadHomeworks() {
      try {
        await this.homeworkStore.fetchStudentHomeworks({
          page: this.pagination.current,
          size: this.pagination.pageSize
        })
        this.updateStatistics()
      } catch (error) {
        console.error('加载作业失败:', error)
      }
    },

    updateStatistics() {
      this.statistics = {
        total: this.homeworks.length,
        completed: this.homeworks.filter(h => h.status === 'completed').length,
        inProgress: this.homeworks.filter(h => h.status === 'in_progress').length,
        averageCompletionRate: this.calculateAverageCompletionRate()
      }
    },

    calculateAverageCompletionRate() {
      if (this.homeworks.length === 0) return 0
      const totalProgress = this.homeworks.reduce((sum, h) => sum + (h.progress || 0), 0)
      return Math.round(totalProgress / this.homeworks.length)
    },

    async handlePaginationChange(page, pageSize) {
      this.pagination.current = page
      this.pagination.pageSize = pageSize
      await this.loadHomeworks()
    },

    handleFilterChange(filter) {
      if (filter === 'all') {
        Object.keys(this.filters).forEach(key => {
          this.filters[key] = key === 'all'
        })
      } else {
        this.filters.all = false
      }
    },

    async startStudy(record) {
      try {
        await this.homeworkStore.startHomework(record.id)
        this.$router.push(`/student/study?homework=${record.id}`)
      } catch (error) {
        console.error('开始作业失败:', error)
      }
    },

    async viewResult(record) {
      try {
        const result = await this.homeworkStore.getHomeworkResult(record.id)
        // 可以显示结果模态框或跳转到结果页面
        console.log('作业结果:', result)
      } catch (error) {
        console.error('获取结果失败:', error)
      }
    },

    viewDetail(record) {
      this.homeworkStore.setCurrentHomework(record)
      // 可以显示详情模态框或跳转到详情页面
      console.log('查看作业详情:', record)
    },

    getStatusColor(status) {
      const colors = {
        'pending': 'red',
        'in_progress': 'orange',
        'completed': 'green'
      }
      return colors[status] || 'default'
    },

    getStatusText(status) {
      const texts = {
        'pending': '待完成',
        'in_progress': '进行中',
        'completed': '已完成'
      }
      return texts[status] || status
    },

    getProgressStatus(status) {
      if (status === 'completed') return 'success'
      if (status === 'in_progress') return 'active'
      return 'normal'
    },

    formatDate(dateString) {
      if (!dateString) return ''
      return new Date(dateString).toLocaleDateString()
    },

    isOverdue(dueDate) {
      if (!dueDate) return false
      return new Date(dueDate) < new Date()
    }
  }
}
</script>

<style scoped>
.text-red-500 {
  color: #ef4444;
}
</style>