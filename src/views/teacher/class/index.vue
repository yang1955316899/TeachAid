<template>
  <div>
    <a-card title="班级管理">
      <template #extra>
        <a-button type="primary">
          创建班级
        </a-button>
      </template>
      
      <a-table
        :columns="columns"
        :data-source="classes"
        :pagination="pagination"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small">管理学生</a-button>
              <a-button size="small">查看统计</a-button>
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
  name: 'ClassManage',
  data() {
    return {
      columns: [
        {
          title: '班级名称',
          dataIndex: 'name',
          key: 'name'
        },
        {
          title: '年级',
          dataIndex: 'grade',
          key: 'grade'
        },
        {
          title: '学科',
          dataIndex: 'subject',
          key: 'subject'
        },
        {
          title: '学生人数',
          dataIndex: 'studentCount',
          key: 'studentCount'
        },
        {
          title: '创建时间',
          dataIndex: 'createTime',
          key: 'createTime'
        },
        {
          title: '操作',
          key: 'action'
        }
      ],
      classes: [
        {
          key: '1',
          name: '高三1班',
          grade: '高三',
          subject: '数学',
          studentCount: 45,
          createTime: '2024-01-10'
        }
      ],
      pagination: {
        current: 1,
        pageSize: 10,
        total: 5
      }
    }
  }
}
</script>