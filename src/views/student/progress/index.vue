<template>
  <div>
    <a-row :gutter="16">
      <a-col :span="24">
        <a-card title="学习进度概览">
          <template #extra>
            <a-button type="primary" :loading="loading" @click="refreshData">
              刷新数据
            </a-button>
          </template>
          <a-row :gutter="16">
            <a-col :span="6">
              <a-statistic
                title="总学习时长"
                :value="progressData.totalHours"
                suffix="小时"
                :value-style="{ color: '#3f8600' }"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic
                title="完成作业数"
                :value="progressData.completedHomework"
                :value-style="{ color: '#1890ff' }"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic
                title="AI对话次数"
                :value="progressData.chatCount"
                :value-style="{ color: '#722ed1' }"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic
                title="平均分数"
                :value="progressData.averageScore"
                suffix="分"
                :value-style="{ color: '#eb2f96' }"
              />
            </a-col>
          </a-row>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="12">
        <a-card title="学科掌握情况">
          <a-list
            :data-source="subjectProgress"
            item-layout="horizontal"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :title="item.subject" />
                <div style="width: 200px">
                  <a-progress
                    :percent="item.progress"
                    :status="item.progress >= 80 ? 'success' : 'active'"
                  />
                </div>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
      
      <a-col :span="12">
        <a-card title="薄弱知识点">
          <a-list
            :data-source="weakPoints"
            item-layout="horizontal"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta
                  :title="item.topic"
                  :description="item.suggestion"
                />
                <a-tag color="orange">需加强</a-tag>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="24">
        <a-card title="最近学习记录">
          <a-table
            :columns="recordColumns"
            :data-source="studyRecords"
            :pagination="{ pageSize: 5 }"
          />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script>
import { analyticsApi } from '@/api/analytics'
import { useAuthStore } from '@/stores/auth'
import { message } from 'ant-design-vue'

export default {
  name: 'StudentProgress',
  data() {
    return {
      loading: false,
      progressData: {
        totalHours: 0,
        completedHomework: 0,
        chatCount: 0,
        averageScore: 0
      },
      subjectProgress: [],
      weakPoints: [],
      recordColumns: [
        {
          title: '日期',
          dataIndex: 'date',
          key: 'date'
        },
        {
          title: '作业/练习',
          dataIndex: 'homework',
          key: 'homework'
        },
        {
          title: '学习时长',
          dataIndex: 'duration',
          key: 'duration'
        },
        {
          title: 'AI对话次数',
          dataIndex: 'chatCount',
          key: 'chatCount'
        },
        {
          title: '完成度',
          dataIndex: 'completion',
          key: 'completion'
        }
      ],
      studyRecords: [],
      days: 30 // 默认查询30天数据
    }
  },
  async mounted() {
    await this.loadProgressData()
  },
  methods: {
    async loadProgressData() {
      try {
        this.loading = true
        const authStore = useAuthStore()
        const currentUser = authStore.user

        if (!currentUser?.user_id) {
          message.error('用户信息未找到，请重新登录')
          return
        }

        const response = await analyticsApi.getStudentReport(currentUser.user_id, {
          days: this.days
        })

        if (response.success) {
          const data = response.data
          this.processProgressData(data)
        } else {
          message.error(response.message || '获取学习进度失败')
        }
      } catch (error) {
        console.error('加载学习进度数据失败:', error)
        message.error('加载学习进度数据失败')
      } finally {
        this.loading = false
      }
    },

    processProgressData(data) {
      // 处理统计数据
      const learning = data.learning_summary || {}
      const homework = data.homework_summary || {}

      this.progressData = {
        // 估算总学习时长 (假设每次对话平均5分钟)
        totalHours: ((learning.total_chat_sessions || 0) * learning.average_session_length * 5 / 60).toFixed(1),
        completedHomework: homework.total_homeworks || 0,
        chatCount: learning.total_chat_sessions || 0,
        // 用完成率代替平均分数
        averageScore: homework.average_completion_rate || 0
      }

      // 处理学科掌握情况
      if (learning.most_active_subject) {
        this.subjectProgress = [
          {
            subject: learning.most_active_subject,
            progress: Math.min(90, homework.average_completion_rate || 50)
          },
          { subject: '其他学科', progress: 60 }
        ]
      } else {
        this.subjectProgress = [
          { subject: '暂无数据', progress: 0 }
        ]
      }

      // 处理薄弱知识点
      const weakKnowledge = data.weak_knowledge_points || []
      this.weakPoints = weakKnowledge.slice(0, 5).map(point => ({
        topic: point,
        suggestion: '建议加强练习和复习'
      }))

      // 如果没有薄弱知识点，显示默认信息
      if (this.weakPoints.length === 0) {
        this.weakPoints = [
          {
            topic: '暂无薄弱知识点',
            suggestion: '继续保持良好的学习状态'
          }
        ]
      }

      // 学习记录暂时使用模拟数据，后续可从其他API获取
      this.studyRecords = [
        {
          key: '1',
          date: new Date().toISOString().split('T')[0],
          homework: '最近学习活动',
          duration: `${this.progressData.totalHours}小时`,
          chatCount: this.progressData.chatCount,
          completion: `${this.progressData.averageScore}%`
        }
      ]
    },

    async refreshData() {
      await this.loadProgressData()
      message.success('数据已刷新')
    }
  }
}
</script>