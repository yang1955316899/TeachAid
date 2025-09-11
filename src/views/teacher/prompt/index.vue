<template>
  <div>
    <a-card title="提示词管理">
      <template #extra>
        <a-button type="primary">
          创建提示词模板
        </a-button>
      </template>
      
      <a-table
        :columns="columns"
        :data-source="prompts"
        :pagination="pagination"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small">编辑</a-button>
              <a-button size="small">测试</a-button>
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
  name: 'PromptManage',
  data() {
    return {
      columns: [
        {
          title: '模板名称',
          dataIndex: 'name',
          key: 'name'
        },
        {
          title: '适用学科',
          dataIndex: 'subject',
          key: 'subject'
        },
        {
          title: '题目类型',
          dataIndex: 'questionType',
          key: 'questionType'
        },
        {
          title: '使用次数',
          dataIndex: 'usageCount',
          key: 'usageCount'
        },
        {
          title: '质量评分',
          dataIndex: 'qualityScore',
          key: 'qualityScore'
        },
        {
          title: '操作',
          key: 'action'
        }
      ],
      prompts: [
        {
          key: '1',
          name: '数学计算题改写',
          subject: '数学',
          questionType: '计算题',
          usageCount: 128,
          qualityScore: '8.5分'
        }
      ],
      pagination: {
        current: 1,
        pageSize: 10,
        total: 8
      }
    }
  }
}
</script>