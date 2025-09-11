<template>
  <div>
    <a-card title="我的作业">
      <a-table
        :columns="columns"
        :data-source="homeworks"
        :pagination="pagination"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ record.status }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button
                v-if="record.status === '待完成'"
                size="small"
                type="primary"
                @click="startStudy(record)"
              >
                开始学习
              </a-button>
              <a-button
                v-else
                size="small"
                @click="viewResult(record)"
              >
                查看结果
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script>
export default {
  name: 'StudentHomework',
  data() {
    return {
      columns: [
        {
          title: '作业标题',
          dataIndex: 'title',
          key: 'title'
        },
        {
          title: '学科',
          dataIndex: 'subject',
          key: 'subject'
        },
        {
          title: '题目数量',
          dataIndex: 'questionCount',
          key: 'questionCount'
        },
        {
          title: '截止时间',
          dataIndex: 'dueDate',
          key: 'dueDate'
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
      homeworks: [
        {
          key: '1',
          title: '数学练习册第三章',
          subject: '数学',
          questionCount: 15,
          dueDate: '2024-01-20',
          status: '待完成'
        },
        {
          key: '2',
          title: '英语阅读理解练习',
          subject: '英语',
          questionCount: 8,
          dueDate: '2024-01-18',
          status: '已完成'
        }
      ],
      pagination: {
        current: 1,
        pageSize: 10,
        total: 15
      }
    }
  },
  methods: {
    getStatusColor(status) {
      const colorMap = {
        '待完成': 'red',
        '进行中': 'orange',
        '已完成': 'green'
      }
      return colorMap[status] || 'default'
    },
    startStudy(record) {
      this.$router.push(`/student/study?homework=${record.key}`)
    },
    viewResult(record) {
      console.log('查看结果:', record)
    }
  }
}
</script>