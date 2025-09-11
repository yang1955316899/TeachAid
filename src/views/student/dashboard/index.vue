<template>
  <div>
    <a-row :gutter="16">
      <a-col :span="8">
        <a-card>
          <a-statistic
            title="待完成作业"
            :value="stats.pendingHomework"
            :value-style="{ color: '#cf1322' }"
          />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card>
          <a-statistic
            title="已完成作业"
            :value="stats.completedHomework"
            :value-style="{ color: '#3f8600' }"
          />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card>
          <a-statistic
            title="学习时长(小时)"
            :value="stats.studyHours"
            :value-style="{ color: '#1890ff' }"
          />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="12">
        <a-card title="最近作业">
          <a-list
            :data-source="recentHomework"
            item-layout="horizontal"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta
                  :title="item.title"
                  :description="`截止时间: ${item.dueDate}`"
                />
                <div>
                  <a-tag :color="item.status === '待完成' ? 'red' : 'green'">
                    {{ item.status }}
                  </a-tag>
                </div>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="学习建议">
          <a-list
            :data-source="suggestions"
            item-layout="horizontal"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta
                  :title="item.title"
                  :description="item.description"
                />
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script>
export default {
  name: 'StudentDashboard',
  data() {
    return {
      stats: {
        pendingHomework: 3,
        completedHomework: 12,
        studyHours: 28.5
      },
      recentHomework: [
        {
          title: '数学练习册第三章',
          dueDate: '2024-01-20',
          status: '待完成'
        },
        {
          title: '英语阅读理解练习',
          dueDate: '2024-01-18',
          status: '已完成'
        }
      ],
      suggestions: [
        {
          title: '加强数学练习',
          description: '建议多做二次函数相关题目'
        },
        {
          title: '英语单词积累',
          description: '每日背诵20个新单词'
        }
      ]
    }
  }
}
</script>