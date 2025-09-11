<template>
  <div>
    <a-card title="作业管理">
      <template #extra>
        <a-button type="primary">
          创建作业
        </a-button>
      </template>
      
      <a-table
        :columns="columns"
        :data-source="homeworks"
        :pagination="pagination"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small">查看详情</a-button>
              <a-button size="small">学习进度</a-button>
              <a-button size="small" danger>删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script>
export default {
  name: 'HomeworkManage',
  data() {
    return {
      columns: [
        {
          title: '作业标题',
          dataIndex: 'title',
          key: 'title'
        },
        {
          title: '班级',
          dataIndex: 'className',
          key: 'className'
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
          title: '完成率',
          dataIndex: 'completionRate',
          key: 'completionRate'
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
          className: '高三1班',
          questionCount: 15,
          dueDate: '2024-01-20',
          completionRate: '85%'
        }
      ],
      pagination: {
        current: 1,
        pageSize: 10,
        total: 10
      }
    }
  }
}
</script>