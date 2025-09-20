<template>
  <div>
    <a-card title="授课关系管理" style="margin-bottom: 16px">
      <template #extra>
        <a-button type="primary" @click="showCreateModal = true">
          创建授课关系
        </a-button>
      </template>

      <!-- 搜索区域 -->
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="6">
          <a-select
            v-model:value="searchParams.class_id"
            placeholder="选择班级"
            allow-clear
            @change="handleSearch"
            :loading="classLoading"
          >
            <a-select-option v-for="classItem in classOptions" :key="classItem.value" :value="classItem.value">
              {{ classItem.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="searchParams.subject_id"
            placeholder="选择学科"
            allow-clear
            @change="handleSearch"
            :loading="subjectLoading"
          >
            <a-select-option v-for="subject in subjectOptions" :key="subject.value" :value="subject.value">
              {{ subject.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="searchParams.term" placeholder="学期" allow-clear @change="handleSearch">
            <a-select-option value="2024春季">2024春季</a-select-option>
            <a-select-option value="2024秋季">2024秋季</a-select-option>
            <a-select-option value="2025春季">2025春季</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button type="primary" @click="handleSearch">搜索</a-button>
          <a-button style="margin-left: 8px" @click="resetSearch">重置</a-button>
        </a-col>
      </a-row>

      <a-table
        :columns="columns"
        :data-source="teachings"
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
          <template v-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'green' : 'red'">
              {{ record.is_active ? '激活' : '禁用' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button
                size="small"
                :type="record.is_active ? 'default' : 'primary'"
                @click="toggleStatus(record)"
              >
                {{ record.is_active ? '禁用' : '激活' }}
              </a-button>
              <a-popconfirm
                title="确定要删除这个授课关系吗？"
                @confirm="deleteTeaching(record)"
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

    <!-- 创建授课关系模态框 -->
    <a-modal
      v-model:open="showCreateModal"
      title="创建授课关系"
      width="600px"
      @ok="handleCreate"
      :okButtonProps="{ loading: loading }"
    >
      <a-form layout="vertical" :model="form">
        <a-form-item label="选择班级" required>
          <a-select
            v-model:value="form.class_id"
            placeholder="请选择班级"
            :loading="classLoading"
          >
            <a-select-option v-for="classItem in classOptions" :key="classItem.value" :value="classItem.value">
              {{ classItem.label }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="选择学科" required>
          <a-select
            v-model:value="form.subject_id"
            placeholder="请选择学科"
            :loading="subjectLoading"
          >
            <a-select-option v-for="subject in subjectOptions" :key="subject.value" :value="subject.value">
              {{ subject.label }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="学期">
          <a-input v-model:value="form.term" placeholder="如：2024春季" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { teachingApi } from '@/api/teaching'
import { classApi } from '@/api/class'
import { eduApi } from '@/api/edu'
import { message } from 'ant-design-vue'

export default {
  name: 'TeachingManage',
  data() {
    return {
      showCreateModal: false,
      teachings: [],
      loading: false,
      pagination: {
        current: 1,
        pageSize: 10,
        total: 0
      },
      searchParams: {
        class_id: '',
        subject_id: '',
        term: ''
      },
      form: {
        class_id: '',
        subject_id: '',
        term: '2024春季'
      },
      columns: [
        {
          title: '班级名称',
          dataIndex: 'class_name',
          key: 'class_name'
        },
        {
          title: '学科',
          dataIndex: 'subject_name',
          key: 'subject_name'
        },
        {
          title: '学期',
          dataIndex: 'term',
          key: 'term'
        },
        {
          title: '状态',
          dataIndex: 'is_active',
          key: 'is_active'
        },
        {
          title: '创建时间',
          dataIndex: 'created_time',
          key: 'created_time',
          customRender: ({ record }) => {
            return record.created_time ? new Date(record.created_time).toLocaleDateString() : '--'
          }
        },
        {
          title: '操作',
          key: 'action'
        }
      ],
      classOptions: [],
      classLoading: false,
      subjectOptions: [],
      subjectLoading: false
    }
  },
  mounted() {
    this.loadTeachings()
    this.loadClasses()
    this.loadSubjects()
    this.handleQueryParams()
  },
  methods: {
    handleQueryParams() {
      // 处理从其他页面传递过来的查询参数
      const { classId, className } = this.$route.query
      if (classId) {
        this.searchParams.class_id = classId
        // 可以显示一个提示消息
        if (className) {
          this.$message.info(`正在查看班级"${className}"的授课关系`)
        }
      }
    },

    async loadTeachings() {
      this.loading = true
      try {
        const response = await teachingApi.getMyTeaching({
          page: this.pagination.current,
          size: this.pagination.pageSize,
          ...this.searchParams
        })

        if (response.success) {
          this.teachings = response.data.items || []
          this.pagination.total = response.data.total || 0
        }
      } catch (error) {
        console.error('加载授课关系失败:', error)
        message.error('加载授课关系失败')
      } finally {
        this.loading = false
      }
    },

    async loadClasses() {
      this.classLoading = true
      try {
        const response = await classApi.getClasses({ page: 1, size: 100 })
        if (response.success) {
          this.classOptions = (response.data.items || []).map(item => ({
            label: item.name,
            value: item.id
          }))
        }
      } catch (error) {
        console.error('加载班级列表失败:', error)
      } finally {
        this.classLoading = false
      }
    },

    async loadSubjects() {
      this.subjectLoading = true
      try {
        const response = await eduApi.getSubjects()
        if (response.success) {
          this.subjectOptions = (response.data.items || []).map(item => ({
            label: item.name,
            value: item.id
          }))
        }
      } catch (error) {
        console.error('加载学科列表失败:', error)
      } finally {
        this.subjectLoading = false
      }
    },

    async handleSearch() {
      this.pagination.current = 1
      await this.loadTeachings()
    },

    resetSearch() {
      this.searchParams = {
        class_id: '',
        subject_id: '',
        term: ''
      }
      this.handleSearch()
    },

    async handlePaginationChange(page, pageSize) {
      this.pagination.current = page
      this.pagination.pageSize = pageSize
      await this.loadTeachings()
    },

    async handleCreate() {
      if (!this.form.class_id || !this.form.subject_id) {
        message.warning('请填写必填字段')
        return
      }

      try {
        const response = await teachingApi.createTeaching(this.form)
        if (response.success) {
          message.success('授课关系创建成功')
          this.showCreateModal = false
          this.resetForm()
          await this.loadTeachings()
        }
      } catch (error) {
        console.error('创建授课关系失败:', error)
        message.error('创建授课关系失败')
      }
    },

    async toggleStatus(record) {
      try {
        const response = await teachingApi.updateTeaching(record.id, {
          is_active: !record.is_active
        })
        if (response.success) {
          message.success('状态更新成功')
          await this.loadTeachings()
        }
      } catch (error) {
        console.error('更新状态失败:', error)
        message.error('更新状态失败')
      }
    },

    async deleteTeaching(record) {
      try {
        const response = await teachingApi.deleteTeaching(record.id)
        if (response.success) {
          message.success('删除成功')
          await this.loadTeachings()
        }
      } catch (error) {
        console.error('删除失败:', error)
        message.error('删除失败')
      }
    },

    resetForm() {
      this.form = {
        class_id: '',
        subject_id: '',
        term: '2024春季'
      }
    }
  }
}
</script>