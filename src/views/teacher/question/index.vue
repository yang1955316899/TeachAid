<template>
  <div>
    <a-card title="题目管理" style="margin-bottom: 16px">
      <template #extra>
        <a-button type="primary" @click="showUploadModal = true">
          上传题目
        </a-button>
      </template>
      
      <!-- 搜索区域 -->
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="4">
          <a-select v-model:value="searchParams.subject" placeholder="学科" allow-clear @change="handleSearch">
            <a-select-option value="数学">数学</a-select-option>
            <a-select-option value="语文">语文</a-select-option>
            <a-select-option value="英语">英语</a-select-option>
            <a-select-option value="物理">物理</a-select-option>
            <a-select-option value="化学">化学</a-select-option>
            <a-select-option value="生物">生物</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="searchParams.questionType" placeholder="题目类型" allow-clear @change="handleSearch">
            <a-select-option value="选择题">选择题</a-select-option>
            <a-select-option value="填空题">填空题</a-select-option>
            <a-select-option value="解答题">解答题</a-select-option>
            <a-select-option value="综合题">综合题</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="searchParams.difficulty" placeholder="难度" allow-clear @change="handleSearch">
            <a-select-option value="简单">简单</a-select-option>
            <a-select-option value="中等">中等</a-select-option>
            <a-select-option value="困难">困难</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="8">
          <a-input-search
            v-model:value="searchParams.keyword"
            placeholder="搜索题目内容"
            enter-button
            @search="handleSearch"
          />
        </a-col>
      </a-row>
      
      <a-table
        :columns="columns"
        :data-source="questions"
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
          <template v-if="column.key === 'created_at'">
            {{ new Date(record.created_at).toLocaleDateString() }}
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="viewQuestion(record)">查看</a-button>
              <a-button 
                size="small" 
                type="primary" 
                :disabled="record.rewritten_answer"
                @click="rewriteAnswer(record)"
              >
                {{ record.rewritten_answer ? '已改写' : '改写答案' }}
              </a-button>
              <a-popconfirm
                title="确定要删除这个题目吗？"
                @confirm="deleteQuestion(record)"
                ok-text="确定"
                cancel-text="取消"
              >
                <a-button size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 上传模态框 -->
    <a-modal
      v-model:open="showUploadModal"
      title="上传题目"
      width="700px"
      @ok="handleUpload"
      :okButtonProps="{ loading: loading }"
    >
      <a-form layout="vertical">
        <a-form-item label="上传方式">
          <a-radio-group v-model:value="uploadType">
            <a-radio value="file">文件上传</a-radio>
            <a-radio value="text">手动输入</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item v-if="uploadType === 'file'" label="选择文件">
          <a-upload-dragger
            name="file"
            :multiple="false"
            :before-upload="beforeUpload"
            :customRequest="handleFileUpload"
            :showUploadList="false"
          >
            <p class="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p class="ant-upload-hint">
              支持 PDF、JPG、PNG、TXT 格式，文件大小不超过 10MB
            </p>
          </a-upload-dragger>
        </a-form-item>

        <template v-if="uploadType === 'text'">
          <a-form-item label="题目标题">
            <a-input v-model:value="form.title" placeholder="请输入题目标题（可选）" />
          </a-form-item>
          
          <a-form-item label="学科">
            <a-select v-model:value="form.subject" placeholder="请选择学科">
              <a-select-option value="数学">数学</a-select-option>
              <a-select-option value="语文">语文</a-select-option>
              <a-select-option value="英语">英语</a-select-option>
              <a-select-option value="物理">物理</a-select-option>
              <a-select-option value="化学">化学</a-select-option>
              <a-select-option value="生物">生物</a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="题目类型">
            <a-select v-model:value="form.questionType" placeholder="请选择题目类型">
              <a-select-option value="选择题">选择题</a-select-option>
              <a-select-option value="填空题">填空题</a-select-option>
              <a-select-option value="解答题">解答题</a-select-option>
              <a-select-option value="综合题">综合题</a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="难度">
            <a-select v-model:value="form.difficulty" placeholder="请选择难度">
              <a-select-option value="简单">简单</a-select-option>
              <a-select-option value="中等">中等</a-select-option>
              <a-select-option value="困难">困难</a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="适用年级">
            <a-input v-model:value="form.gradeLevel" placeholder="请输入适用年级（如：初中一年级）" />
          </a-form-item>
          
          <a-form-item label="题目内容" required>
            <a-textarea
              v-model:value="textContent"
              placeholder="请输入题目内容"
              :rows="6"
              show-count
              :maxlength="5000"
            />
          </a-form-item>
          
          <a-form-item label="原始答案">
            <a-textarea
              v-model:value="form.originalAnswer"
              placeholder="请输入原始答案（可选，系统会自动改写为引导式答案）"
              :rows="4"
              show-count
              :maxlength="3000"
            />
          </a-form-item>
        </template>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { InboxOutlined } from '@ant-design/icons-vue'
import { useQuestionStore } from '@/stores/question'
import { storeToRefs } from 'pinia'

export default {
  name: 'QuestionManage',
  components: {
    InboxOutlined
  },
  data() {
    return {
      showUploadModal: false,
      showCreateModal: false,
      uploadType: 'file',
      textContent: '',
      form: {
        title: '',
        content: '',
        originalAnswer: '',
        subject: '',
        questionType: '',
        difficulty: '',
        gradeLevel: ''
      },
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
          dataIndex: 'question_type',
          key: 'question_type'
        },
        {
          title: '难度',
          dataIndex: 'difficulty',
          key: 'difficulty'
        },
        {
          title: '创建时间',
          dataIndex: 'created_at',
          key: 'created_at'
        },
        {
          title: '操作',
          key: 'action'
        }
      ],
      searchParams: {
        subject: '',
        questionType: '',
        difficulty: '',
        keyword: ''
      }
    }
  },
  computed: {
    questionStore() {
      return useQuestionStore()
    }
  },
  setup() {
    const questionStore = useQuestionStore()
    const { questions, loading, pagination } = storeToRefs(questionStore)
    
    return {
      questions,
      loading,
      pagination
    }
  },
  mounted() {
    this.loadQuestions()
  },
  methods: {
    async loadQuestions() {
      try {
        await this.questionStore.fetchQuestions({
          page: this.pagination.current,
          size: this.pagination.pageSize,
          ...this.searchParams
        })
      } catch (error) {
        console.error('加载题目失败:', error)
      }
    },

    async handleSearch() {
      this.pagination.current = 1
      await this.loadQuestions()
    },

    async handlePaginationChange(page, pageSize) {
      this.pagination.current = page
      this.pagination.pageSize = pageSize
      await this.loadQuestions()
    },

    async handleUpload() {
      if (this.uploadType === 'text' && this.textContent.trim()) {
        // 文本方式创建题目
        const questionData = {
          title: this.form.title || '手动创建题目',
          content: this.textContent,
          original_answer: this.form.originalAnswer,
          subject: this.form.subject,
          question_type: this.form.questionType,
          difficulty: this.form.difficulty,
          grade_level: this.form.gradeLevel
        }
        
        try {
          await this.questionStore.createQuestion(questionData)
          this.showUploadModal = false
          this.resetForm()
          await this.loadQuestions()
        } catch (error) {
          console.error('创建题目失败:', error)
        }
      } else {
        this.showUploadModal = false
      }
    },

    handleFileChange(info) {
      if (info.file.status === 'done') {
        this.$message.success('文件上传成功')
        this.showUploadModal = false
        this.loadQuestions()
      } else if (info.file.status === 'error') {
        this.$message.error('文件上传失败')
      }
    },

    beforeUpload(file) {
      // 验证文件类型
      const isAllowedType = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf', 'text/plain'].includes(file.type)
      if (!isAllowedType) {
        this.$message.error('只支持 JPG、PNG、PDF、TXT 格式')
        return false
      }
      
      // 验证文件大小（10MB）
      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        this.$message.error('文件大小不能超过 10MB')
        return false
      }
      
      return true
    },

    async handleFileUpload(file) {
      try {
        await this.questionStore.uploadQuestion(file)
        this.showUploadModal = false
        await this.loadQuestions()
      } catch (error) {
        console.error('文件上传失败:', error)
      }
    },

    viewQuestion(record) {
      this.questionStore.setCurrentQuestion(record)
      // 可以跳转到详情页或显示详情模态框
      console.log('查看题目:', record)
    },

    async rewriteAnswer(record) {
      try {
        await this.questionStore.rewriteAnswer(record.id, {
          template_id: 'default',
          style: 'guided'
        })
        await this.loadQuestions()
      } catch (error) {
        console.error('改写答案失败:', error)
      }
    },

    async deleteQuestion(record) {
      try {
        await this.questionStore.deleteQuestion(record.id)
      } catch (error) {
        console.error('删除题目失败:', error)
      }
    },

    resetForm() {
      this.form = {
        title: '',
        content: '',
        originalAnswer: '',
        subject: '',
        questionType: '',
        difficulty: '',
        gradeLevel: ''
      }
      this.textContent = ''
    }
  }
}
</script>