<template>
  <div>
    <a-card title="作业管理" style="margin-bottom: 16px">
      <template #extra>
        <a-button type="primary" @click="showCreateModal = true">
          创建作业
        </a-button>
      </template>
      
      <!-- 搜索区域 -->
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="6">
          <a-input
            v-model:value="searchParams.keyword"
            placeholder="搜索作业标题"
            @pressEnter="handleSearch"
          />
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="searchParams.status" placeholder="状态" allow-clear @change="handleSearch">
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="published">已发布</a-select-option>
            <a-select-option value="closed">已截止</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button type="primary" @click="handleSearch">搜索</a-button>
          <a-button style="margin-left: 8px" @click="resetSearch">重置</a-button>
        </a-col>
      </a-row>
      
      <a-table
        :columns="columns"
        :data-source="homeworks"
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
          <template v-if="column.key === 'dueDate'">
            {{ new Date(record.due_date).toLocaleDateString() }}
          </template>
          <template v-if="column.key === 'completionRate'">
            <a-progress 
              :percent="record.completion_rate || 0" 
              :show-info="true"
              size="small"
            />
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="viewHomework(record)">查看详情</a-button>
              <a-button size="small" @click="viewProgress(record)">学习进度</a-button>
              <a-button 
                v-if="record.status === 'draft'"
                size="small" 
                type="primary" 
                @click="publishHomework(record)"
              >
                发布
              </a-button>
              <a-button 
                v-if="record.status === 'published'"
                size="small" 
                type="primary" 
                danger 
                @click="closeHomework(record)"
              >
                截止
              </a-button>
              <a-popconfirm
                title="确定要删除这个作业吗？"
                @confirm="deleteHomework(record)"
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

    <!-- 创建作业模态框 -->
    <a-modal
      v-model:open="showCreateModal"
      title="创建作业"
      width="800px"
      @ok="handleCreate"
      :okButtonProps="{ loading: loading }"
    >
      <a-form layout="vertical" :model="form">
        <a-form-item label="作业标题" required>
          <a-input v-model:value="form.title" placeholder="请输入作业标题" />
        </a-form-item>
        
        <a-form-item label="作业描述">
          <a-textarea
            v-model:value="form.description"
            placeholder="请输入作业描述"
            :rows="4"
            show-count
            :maxlength="1000"
          />
        </a-form-item>
        
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="选择班级" required>
              <a-select
                v-model:value="form.classId"
                placeholder="请选择班级"
                mode="multiple"
              >
                <a-select-option value="1">高三1班</a-select-option>
                <a-select-option value="2">高三2班</a-select-option>
                <a-select-option value="3">高三3班</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="截止时间" required>
              <a-date-picker
                v-model:value="form.dueDate"
                style="width: 100%"
                show-time
                placeholder="请选择截止时间"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-form-item label="选择题目" required>
          <a-table
            :columns="questionColumns"
            :data-source="availableQuestions"
            :row-selection="rowSelection"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'difficulty'">
                <a-tag :color="getDifficultyColor(record.difficulty)">
                  {{ record.difficulty }}
                </a-tag>
              </template>
            </template>
          </a-table>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 进度查看模态框 -->
    <a-modal
      v-model:open="showProgressModal"
      title="作业学习进度"
      width="600px"
      :footer="null"
    >
      <div v-if="progressData">
        <a-descriptions bordered>
          <a-descriptions-item label="总学生数">{{ progressData.total_students }}</a-descriptions-item>
          <a-descriptions-item label="已完成">{{ progressData.completed_students }}</a-descriptions-item>
          <a-descriptions-item label="未完成">{{ progressData.incomplete_students }}</a-descriptions-item>
          <a-descriptions-item label="完成率">{{ progressData.completion_rate }}%</a-descriptions-item>
        </a-descriptions>
        
        <a-table
          :columns="studentProgressColumns"
          :data-source="progressData.students || []"
          size="small"
          style="margin-top: 16px"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="record.completed ? 'green' : 'orange'">
                {{ record.completed ? '已完成' : '未完成' }}
              </a-tag>
            </template>
          </template>
        </a-table>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { useHomeworkStore } from '@/stores/homework'
import { useQuestionStore } from '@/stores/question'
import { storeToRefs } from 'pinia'
import dayjs from 'dayjs'

export default {
  name: 'HomeworkManage',
  data() {
    return {
      showCreateModal: false,
      showProgressModal: false,
      progressData: null,
      form: {
        title: '',
        description: '',
        classId: [],
        dueDate: null,
        questionIds: []
      },
      searchParams: {
        keyword: '',
        status: ''
      },
      columns: [
        {
          title: '作业标题',
          dataIndex: 'title',
          key: 'title'
        },
        {
          title: '班级',
          dataIndex: 'class_name',
          key: 'className'
        },
        {
          title: '题目数量',
          dataIndex: 'question_count',
          key: 'questionCount'
        },
        {
          title: '截止时间',
          dataIndex: 'due_date',
          key: 'dueDate'
        },
        {
          title: '完成率',
          dataIndex: 'completion_rate',
          key: 'completionRate'
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
      questionColumns: [
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
          title: '类型',
          dataIndex: 'question_type',
          key: 'questionType'
        },
        {
          title: '难度',
          dataIndex: 'difficulty',
          key: 'difficulty'
        }
      ],
      studentProgressColumns: [
        {
          title: '学生姓名',
          dataIndex: 'student_name',
          key: 'studentName'
        },
        {
          title: '学号',
          dataIndex: 'student_id',
          key: 'studentId'
        },
        {
          title: '完成时间',
          dataIndex: 'completed_at',
          key: 'completedAt'
        },
        {
          title: '状态',
          dataIndex: 'status',
          key: 'status'
        }
      ],
      selectedRowKeys: []
    }
  },
  computed: {
    homeworkStore() {
      return useHomeworkStore()
    },
    questionStore() {
      return useQuestionStore()
    },
    rowSelection() {
      return {
        selectedRowKeys: this.selectedRowKeys,
        onChange: (selectedRowKeys) => {
          this.selectedRowKeys = selectedRowKeys
          this.form.questionIds = selectedRowKeys
        }
      }
    }
  },
  setup() {
    const homeworkStore = useHomeworkStore()
    const { homeworks, loading, pagination } = storeToRefs(homeworkStore)
    const questionStore = useQuestionStore()
    const { questions: availableQuestions } = storeToRefs(questionStore)
    
    return {
      homeworks,
      loading,
      pagination,
      availableQuestions
    }
  },
  mounted() {
    this.loadHomeworks()
    this.loadAvailableQuestions()
  },
  methods: {
    async loadHomeworks() {
      try {
        await this.homeworkStore.fetchHomeworks({
          page: this.pagination.current,
          size: this.pagination.pageSize,
          ...this.searchParams
        })
      } catch (error) {
        console.error('加载作业失败:', error)
      }
    },

    async loadAvailableQuestions() {
      try {
        await this.questionStore.fetchQuestions({
          page: 1,
          size: 100
        })
      } catch (error) {
        console.error('加载题目失败:', error)
      }
    },

    async handleSearch() {
      this.pagination.current = 1
      await this.loadHomeworks()
    },

    resetSearch() {
      this.searchParams = {
        keyword: '',
        status: ''
      }
      this.handleSearch()
    },

    async handlePaginationChange(page, pageSize) {
      this.pagination.current = page
      this.pagination.pageSize = pageSize
      await this.loadHomeworks()
    },

    async handleCreate() {
      if (!this.form.title || !this.form.classId.length || !this.form.dueDate || !this.form.questionIds.length) {
        this.$message.warning('请填写必填字段')
        return
      }

      const homeworkData = {
        title: this.form.title,
        description: this.form.description,
        class_ids: this.form.classId,
        due_date: this.form.dueDate.format('YYYY-MM-DD HH:mm:ss'),
        question_ids: this.form.questionIds
      }

      try {
        await this.homeworkStore.createHomework(homeworkData)
        this.showCreateModal = false
        this.resetForm()
        await this.loadHomeworks()
      } catch (error) {
        console.error('创建作业失败:', error)
      }
    },

    viewHomework(record) {
      this.homeworkStore.setCurrentHomework(record)
      // 可以跳转到详情页或显示详情模态框
      console.log('查看作业:', record)
    },

    async viewProgress(record) {
      try {
        this.progressData = await this.homeworkStore.fetchHomeworkProgress(record.id)
        this.showProgressModal = true
      } catch (error) {
        console.error('获取进度失败:', error)
      }
    },

    async publishHomework(record) {
      try {
        await this.homeworkStore.publishHomework(record.id)
        await this.loadHomeworks()
      } catch (error) {
        console.error('发布作业失败:', error)
      }
    },

    async closeHomework(record) {
      try {
        await this.homeworkStore.updateHomework(record.id, { status: 'closed' })
        await this.loadHomeworks()
      } catch (error) {
        console.error('截止作业失败:', error)
      }
    },

    async deleteHomework(record) {
      try {
        await this.homeworkStore.deleteHomework(record.id)
      } catch (error) {
        console.error('删除作业失败:', error)
      }
    },

    resetForm() {
      this.form = {
        title: '',
        description: '',
        classId: [],
        dueDate: null,
        questionIds: []
      }
      this.selectedRowKeys = []
    },

    getStatusColor(status) {
      const colors = {
        draft: 'default',
        published: 'green',
        closed: 'red'
      }
      return colors[status] || 'default'
    },

    getStatusText(status) {
      const texts = {
        draft: '草稿',
        published: '已发布',
        closed: '已截止'
      }
      return texts[status] || status
    },

    getDifficultyColor(difficulty) {
      const colors = {
        '简单': 'green',
        '中等': 'orange',
        '困难': 'red'
      }
      return colors[difficulty] || 'default'
    }
  }
}
</script>