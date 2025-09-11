<template>
  <div>
    <a-row :gutter="16">
      <a-col :span="24">
        <a-card title="学习进度概览">
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
export default {
  name: 'StudentProgress',
  data() {
    return {
      progressData: {
        totalHours: 28.5,
        completedHomework: 12,
        chatCount: 156,
        averageScore: 85.2
      },
      subjectProgress: [
        { subject: '数学', progress: 75 },
        { subject: '英语', progress: 88 },
        { subject: '物理', progress: 65 },
        { subject: '化学', progress: 92 }
      ],
      weakPoints: [
        {
          topic: '二次函数图像变换',
          suggestion: '建议多做相关练习题，加强理解'
        },
        {
          topic: '英语时态运用',
          suggestion: '建议复习时态语法规则'
        }
      ],
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
      studyRecords: [
        {
          key: '1',
          date: '2024-01-15',
          homework: '数学练习册第三章',
          duration: '2.5小时',
          chatCount: 15,
          completion: '100%'
        },
        {
          key: '2',
          date: '2024-01-14',
          homework: '英语阅读理解',
          duration: '1.8小时',
          chatCount: 8,
          completion: '100%'
        }
      ]
    }
  }
}
</script>