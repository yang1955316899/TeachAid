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
        <a-col :span="6">
          <a-select
            v-model:value="searchParams.subject"
            placeholder="学科"
            allow-clear
            @change="handleSearch"
            :loading="subjectLoading"
            style="width: 100%"
          >
            <a-select-option v-for="subject in subjectOptions" :key="subject.value" :value="subject.value">
              {{ subject.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="searchParams.questionType"
            placeholder="题目类型"
            allow-clear
            @change="handleSearch"
            style="width: 100%"
          >
            <a-select-option v-for="type in questionTypeOptions" :key="type.value" :value="type.value">
              {{ type.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="searchParams.difficulty"
            placeholder="难度"
            allow-clear
            @change="handleSearch"
            style="width: 100%"
          >
            <a-select-option v-for="level in difficultyOptions" :key="level.value" :value="level.value">
              {{ level.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-input-search
            v-model:value="searchParams.keyword"
            placeholder="搜索题目内容"
            enter-button
            @search="handleSearch"
            style="width: 100%"
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
            <a-select v-model:value="form.subject" placeholder="请选择学科" :loading="subjectLoading">
              <a-select-option v-for="subject in subjectOptions" :key="subject.value" :value="subject.value">
                {{ subject.label }}
              </a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="题目类型">
            <a-select v-model:value="form.questionType" placeholder="请选择题目类型">
              <a-select-option v-for="type in questionTypeOptions" :key="type.value" :value="type.value">
                {{ type.label }}
              </a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="难度">
            <a-select v-model:value="form.difficulty" placeholder="请选择难度">
              <a-select-option v-for="level in difficultyOptions" :key="level.value" :value="level.value">
                {{ level.label }}
              </a-select-option>
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

    <!-- 题目详情模态框 -->
    <a-modal
      v-model:open="showDetailModal"
      title="题目详情"
      width="800px"
      :footer="null"
    >
      <div v-if="currentQuestionDetail" style="max-height: 400px; overflow-y: auto;">
        <a-descriptions bordered column="1">
          <a-descriptions-item label="题目标题">{{ currentQuestionDetail.title || '无标题' }}</a-descriptions-item>
          <a-descriptions-item label="学科">{{ currentQuestionDetail.subject || '未知' }}</a-descriptions-item>
          <a-descriptions-item label="题目类型">{{ currentQuestionDetail.question_type || '未知' }}</a-descriptions-item>
          <a-descriptions-item label="难度">{{ currentQuestionDetail.difficulty || '未知' }}</a-descriptions-item>
          <a-descriptions-item label="创建时间">
            {{ currentQuestionDetail.created_at ? new Date(currentQuestionDetail.created_at).toLocaleString() : '未知' }}
          </a-descriptions-item>
        </a-descriptions>

        <div style="margin-top: 16px;">
          <h4>题目内容:</h4>
          <div style="padding: 12px; background-color: #fafafa; border-radius: 6px; white-space: pre-wrap; margin-bottom: 16px;">
            {{ currentQuestionDetail.content || '暂无内容' }}
          </div>
        </div>

        <div v-if="currentQuestionDetail.original_answer" style="margin-top: 16px;">
          <h4>原始答案:</h4>
          <div style="padding: 12px; background-color: #f6ffed; border-radius: 6px; white-space: pre-wrap; margin-bottom: 16px;">
            {{ currentQuestionDetail.original_answer }}
          </div>
        </div>

        <div v-if="currentQuestionDetail.rewritten_answer" style="margin-top: 16px;">
          <h4>改写答案:</h4>
          <div style="padding: 12px; background-color: #fff7e6; border-radius: 6px; white-space: pre-wrap;">
            {{ currentQuestionDetail.rewritten_answer }}
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { InboxOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useQuestionStore } from '@/stores/question'
import { storeToRefs } from 'pinia'
import { eduApi } from '@/api/edu'

export default {
  name: 'QuestionManage',
  components: {
    InboxOutlined
  },
  data() {
    return {
      showUploadModal: false,
      showCreateModal: false,
      showDetailModal: false,
      currentQuestionDetail: null,
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
      },
      // 动态加载的选项
      subjectOptions: [],
      subjectLoading: false,
      questionTypeOptions: [
        { label: '选择题', value: '选择题' },
        { label: '填空题', value: '填空题' },
        { label: '解答题', value: '解答题' },
        { label: '综合题', value: '综合题' },
        { label: '应用题', value: '应用题' },
        { label: '证明题', value: '证明题' }
      ],
      difficultyOptions: [
        { label: '简单', value: '简单' },
        { label: '中等', value: '中等' },
        { label: '困难', value: '困难' }
      ]
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
    this.loadSubjects()
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

    async loadSubjects() {
      this.subjectLoading = true
      try {
        const response = await eduApi.getSubjects()
        if (response.success) {
          this.subjectOptions = (response.data.items || []).map(item => ({
            label: item.name,
            value: item.name
          }))
        }
      } catch (error) {
        console.error('加载学科列表失败:', error)
        message.error('加载学科列表失败')
      } finally {
        this.subjectLoading = false
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
        message.success('文件上传成功')
        this.showUploadModal = false
        this.loadQuestions()
      } else if (info.file.status === 'error') {
        message.error('文件上传失败')
      }
    },

    beforeUpload(file) {
      // 验证文件类型
      const isAllowedType = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf', 'text/plain'].includes(file.type)
      if (!isAllowedType) {
        message.error('只支持 JPG、PNG、PDF、TXT 格式')
        return false
      }
      
      // 验证文件大小 10MB
      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        message.error('文件大小不能超过 10MB')
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

    async viewQuestion(record) {
      try {
        this.questionStore.setCurrentQuestion(record)
        // 显示题目详情模态框
        this.showQuestionDetail(record)
      } catch (error) {
        console.error('查看题目失败:', error)
        this.$message.error('无法查看题目详情')
      }
    },

    showQuestionDetail(record) {
      this.currentQuestionDetail = record
      this.showDetailModal = true
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