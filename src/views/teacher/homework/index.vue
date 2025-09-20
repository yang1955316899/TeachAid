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
          <a-select v-model:value="searchParams.is_published" placeholder="发布状态" allow-clear @change="handleSearch">
            <a-select-option :value="true">已发布</a-select-option>
            <a-select-option :value="false">未发布</a-select-option>
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
        :rowKey="record => record.id"
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
            {{ record.due_at ? new Date(record.due_at).toLocaleString() : '--' }}
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="record.is_published ? 'green' : 'default'">
              {{ record.is_published ? '已发布' : '未发布' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="viewHomework(record)">查看详情</a-button>
              <a-button size="small" @click="viewProgress(record)">学习进度</a-button>
              <a-button
                v-if="!record.is_published"
                size="small"
                type="primary"
                @click="publishHomework(record)"
              >
                发布
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
                :loading="classLoading"
                :options="classOptions"
              />
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
            :rowKey="record => record.id"
            :row-selection="rowSelection"
            size="small"
            :pagination="false"
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
          <a-descriptions-item label="进行中">{{ progressData.in_progress_students }}</a-descriptions-item>
          <a-descriptions-item label="未开始">{{ progressData.not_started_students }}</a-descriptions-item>
          <a-descriptions-item label="平均完成率">{{ progressData.average_completion_rate }}%</a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>

    <!-- 作业详情模态框 -->
    <a-modal
      v-model:open="showHomeworkDetailModal"
      title="作业详情"
      width="800px"
      :footer="null"
    >
      <div v-if="currentHomeworkDetail" style="max-height: 400px; overflow-y: auto;">
        <a-descriptions bordered column="1">
          <a-descriptions-item label="作业标题">{{ currentHomeworkDetail.title || '无标题' }}</a-descriptions-item>
          <a-descriptions-item label="班级">{{ currentHomeworkDetail.class_name || '未知班级' }}</a-descriptions-item>
          <a-descriptions-item label="题目数量">{{ currentHomeworkDetail.question_count || 0 }}</a-descriptions-item>
          <a-descriptions-item label="截止时间">
            {{ currentHomeworkDetail.due_at ? new Date(currentHomeworkDetail.due_at).toLocaleString() : '无截止时间' }}
          </a-descriptions-item>
          <a-descriptions-item label="发布状态">
            <a-tag :color="currentHomeworkDetail.is_published ? 'success' : 'default'">
              {{ currentHomeworkDetail.is_published ? '已发布' : '未发布' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">
            {{ currentHomeworkDetail.created_at ? new Date(currentHomeworkDetail.created_at).toLocaleString() : '未知' }}
          </a-descriptions-item>
        </a-descriptions>

        <div v-if="currentHomeworkDetail.description" style="margin-top: 16px;">
          <h4>作业描述:</h4>
          <div style="padding: 12px; background-color: #fafafa; border-radius: 6px; white-space: pre-wrap;">
            {{ currentHomeworkDetail.description }}
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { useHomeworkStore } from '@/stores/homework'
import { useQuestionStore } from '@/stores/question'
import { useClassStore } from '@/stores/class'
import { storeToRefs } from 'pinia'

export default {
  name: 'HomeworkManage',
  data() {
    return {
      showCreateModal: false,
      showProgressModal: false,
      showHomeworkDetailModal: false,
      currentHomeworkDetail: null,
      progressData: null,
      form: {
        title: '',
        description: '',
        classId: null,
        dueDate: null,
        questionIds: []
      },
      searchParams: {
        keyword: '',
        is_published: undefined
      },
      columns: [
        { title: '作业标题', dataIndex: 'title', key: 'title' },
        { title: '班级', dataIndex: 'class_name', key: 'className' },
        { title: '题目数量', dataIndex: 'question_count', key: 'questionCount' },
        { title: '截止时间', dataIndex: 'due_at', key: 'dueDate' },
        { title: '发布状态', dataIndex: 'is_published', key: 'status' },
        { title: '操作', key: 'action' }
      ],
      questionColumns: [
        { title: '题目标题', dataIndex: 'title', key: 'title' },
        { title: '学科', dataIndex: 'subject', key: 'subject' },
        { title: '类型', dataIndex: 'question_type', key: 'questionType' },
        { title: '难度', dataIndex: 'difficulty', key: 'difficulty' }
      ],
      selectedRowKeys: [],
      classOptions: [],
      classLoading: false
    }
  },
  computed: {
    homeworkStore() {
      return useHomeworkStore()
    },
    questionStore() {
      return useQuestionStore()
    },
    classStore() {
      return useClassStore()
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

    const classStore = useClassStore()
    const { classes } = storeToRefs(classStore)

    return {
      homeworks,
      loading,
      pagination,
      availableQuestions,
      classes
    }
  },
  mounted() {
    this.loadHomeworks()
    this.loadAvailableQuestions()
    this.loadClasses()
  },
  methods: {
    async loadHomeworks() {
      try {
        await this.homeworkStore.fetchHomeworks({
          page: this.pagination.current,
          size: this.pagination.pageSize,
          keyword: this.searchParams.keyword,
          is_published: this.searchParams.is_published
        })
      } catch (error) {
        console.error('加载作业失败:', error)
      }
    },

    async loadAvailableQuestions() {
      try {
        await this.questionStore.fetchQuestions({ page: 1, size: 100 })
      } catch (error) {
        console.error('加载题目失败:', error)
      }
    },

    async loadClasses() {
      try {
        this.classLoading = true
        const res = await this.classStore.fetchClasses({ page: 1, size: 100 })
        const items = res?.data?.items || this.classes || []
        this.classOptions = (items || []).map(c => ({ label: c.name, value: c.id }))
      } catch (e) {
        console.error('加载班级失败:', e)
        this.classOptions = []
      } finally {
        this.classLoading = false
      }
    },

    async handleSearch() {
      this.pagination.current = 1
      await this.loadHomeworks()
    },

    resetSearch() {
      this.searchParams = { keyword: '', is_published: undefined }
      this.handleSearch()
    },

    async handlePaginationChange(page, pageSize) {
      this.pagination.current = page
      this.pagination.pageSize = pageSize
      await this.loadHomeworks()
    },

    async handleCreate() {
      if (!this.form.title || !this.form.classId || !this.form.dueDate || !this.form.questionIds.length) {
        this.$message.warning('请填写必填字段')
        return
      }

      const homeworkData = {
        title: this.form.title,
        description: this.form.description,
        class_id: this.form.classId,
        due_at: this.form.dueDate?.toDate ? this.form.dueDate.toDate() : new Date(this.form.dueDate),
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

    async viewHomework(record) {
      try {
        // 设置当前作业并获取详细信息
        this.homeworkStore.setCurrentHomework(record)

        // 显示作业详情模态框
        this.showHomeworkDetail(record)
      } catch (error) {
        console.error('查看作业失败:', error)
        this.$message.error('无法查看作业详情')
      }
    },

    showHomeworkDetail(record) {
      this.currentHomeworkDetail = record
      this.showHomeworkDetailModal = true
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
        classId: null,
        dueDate: null,
        questionIds: []
      }
      this.selectedRowKeys = []
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