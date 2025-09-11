<template>
  <div>
    <a-card title="题目管理" style="margin-bottom: 16px">
      <template #extra>
        <a-button type="primary" @click="showUploadModal = true">
          上传题目
        </a-button>
      </template>
      
      <a-table
        :columns="columns"
        :data-source="questions"
        :pagination="pagination"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="viewQuestion(record)">查看</a-button>
              <a-button size="small" @click="rewriteAnswer(record)">改写答案</a-button>
              <a-button size="small" danger @click="deleteQuestion(record)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 上传模态框 -->
    <a-modal
      v-model:open="showUploadModal"
      title="上传题目"
      width="600px"
      @ok="handleUpload"
    >
      <a-form layout="vertical">
        <a-form-item label="上传方式">
          <a-radio-group v-model:value="uploadType">
            <a-radio value="file">文件上传</a-radio>
            <a-radio value="text">文本输入</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item v-if="uploadType === 'file'" label="选择文件">
          <a-upload-dragger
            name="file"
            :multiple="false"
            action="/api/questions/upload"
            @change="handleFileChange"
          >
            <p class="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p class="ant-upload-hint">
              支持 PDF、JPG、PNG 格式
            </p>
          </a-upload-dragger>
        </a-form-item>

        <a-form-item v-if="uploadType === 'text'" label="题目内容">
          <a-textarea
            v-model:value="textContent"
            placeholder="请输入题目内容"
            :rows="6"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { InboxOutlined } from '@ant-design/icons-vue'

export default {
  name: 'QuestionManage',
  components: {
    InboxOutlined
  },
  data() {
    return {
      showUploadModal: false,
      uploadType: 'file',
      textContent: '',
      columns: [
        {
          title: '题目标题',
          dataIndex: 'title',
          key: 'title'
        },
        {
          title: '学科',
          dataIndex: 'subject',
          key: 'subject'
        },
        {
          title: '题目类型',
          dataIndex: 'type',
          key: 'type'
        },
        {
          title: '创建时间',
          dataIndex: 'createTime',
          key: 'createTime'
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
      questions: [
        {
          key: '1',
          title: '二次函数综合应用题',
          subject: '数学',
          type: '解答题',
          createTime: '2024-01-15',
          status: '已改写'
        },
        {
          key: '2',
          title: '英语完形填空',
          subject: '英语',
          type: '选择题',
          createTime: '2024-01-14',
          status: '待改写'
        }
      ],
      pagination: {
        current: 1,
        pageSize: 10,
        total: 20
      }
    }
  },
  methods: {
    handleUpload() {
      console.log('上传题目')
      this.showUploadModal = false
    },
    handleFileChange(info) {
      console.log('文件变化:', info)
    },
    viewQuestion(record) {
      console.log('查看题目:', record)
    },
    rewriteAnswer(record) {
      console.log('改写答案:', record)
    },
    deleteQuestion(record) {
      console.log('删除题目:', record)
    }
  }
}
</script>