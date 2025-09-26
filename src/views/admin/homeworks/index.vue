<template>
  <div class="admin-homeworks">
    <div class="header">
      <h2>作业管理</h2>
    </div>

    <div class="filters">
      <el-form :model="filters" layout="inline">
        <el-form-item label="教师">
          <el-select v-model="filters.teacherId" placeholder="选择教师" clearable>
            <el-option
              v-for="teacher in teachers"
              :key="teacher.id"
              :label="teacher.name"
              :value="teacher.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="filters.classId" placeholder="选择班级" clearable>
            <el-option
              v-for="cls in classes"
              :key="cls.id"
              :label="cls.name"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="选择状态" clearable>
            <el-option label="进行中" value="active" />
            <el-option label="已截止" value="expired" />
            <el-option label="草稿" value="draft" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-table :data="homeworks" v-loading="loading">
      <el-table-column prop="title" label="作业标题" width="200" />
      <el-table-column prop="teacherName" label="创建教师" width="120" />
      <el-table-column prop="className" label="班级" width="150" />
      <el-table-column prop="questionCount" label="题目数量" width="100" />
      <el-table-column prop="submissionCount" label="提交数/总数" width="120">
        <template #default="{ row }">
          {{ row.submissionCount }}/{{ row.totalStudents }}
        </template>
      </el-table-column>
      <el-table-column prop="dueDate" label="截止时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.dueDate) }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetails(row)">详情</el-button>
          <el-button size="small" type="info" @click="viewProgress(row)">进度</el-button>
          <el-dropdown>
            <el-button size="small">
              更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="extendDeadline(row)">延期</el-dropdown-item>
                <el-dropdown-item @click="exportReport(row)">导出报告</el-dropdown-item>
                <el-dropdown-item @click="sendReminder(row)">发送提醒</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import adminApi from '@/api/admin'

const loading = ref(false)
const homeworks = ref([])
const teachers = ref([])
const classes = ref([])

const filters = reactive({
  teacherId: '',
  classId: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const getStatusType = (status) => {
  const typeMap = {
    'active': 'success',
    'expired': 'danger',
    'draft': 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'active': '进行中',
    'expired': '已截止',
    'draft': '草稿'
  }
  return textMap[status] || '未知'
}

const formatDate = (date) => {
  return new Date(date).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.size,
      creator_id: filters.teacherId,
      class_id: filters.classId,
      is_published: filters.status === 'active' ? 'true' :
                    filters.status === 'draft' ? 'false' : ''
    }

    // 移除空参数
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })

    const response = await adminApi.getHomeworks(params)

    if (response.success) {
      const items = response.data.items || []
      homeworks.value = items.map(item => ({
        id: item.id,
        title: item.title,
        teacherName: item.creator_name || '未知',
        className: item.class_name || '未分配',
        questionCount: item.question_count || 0,
        submissionCount: item.completed_students || 0,
        totalStudents: item.total_students || 0,
        dueDate: item.due_at,
        status: item.is_published ? 'active' : 'draft'
      }))
      pagination.total = response.data.total || 0
    } else {
      ElMessage.error(response.message || '获取作业列表失败')
    }
  } catch (error) {
    console.error('加载作业数据失败:', error)
    ElMessage.error('加载作业数据失败')
  } finally {
    loading.value = false
  }
}

const loadTeachers = async () => {
  try {
    const response = await adminApi.getTeachers()
    if (response.success) {
      teachers.value = response.data.items.map(teacher => ({
        id: teacher.user_id,
        name: teacher.user_full_name || teacher.user_name
      }))
    }
  } catch (error) {
    console.error('加载教师列表失败:', error)
  }
}

const loadClasses = async () => {
  try {
    const response = await adminApi.getClasses()
    if (response.success) {
      classes.value = response.data.items.map(cls => ({
        id: cls.id,
        name: cls.name
      }))
    }
  } catch (error) {
    console.error('加载班级列表失败:', error)
  }
}

const search = () => {
  pagination.page = 1
  loadData()
}

const resetFilters = () => {
  Object.assign(filters, {
    teacherId: '',
    classId: '',
    status: ''
  })
  search()
}

const handleSizeChange = (size) => {
  pagination.size = size
  loadData()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  loadData()
}

const viewDetails = async (row) => {
  try {
    const response = await adminApi.getHomeworkDetail(row.id)
    if (response.success) {
      ElMessageBox.alert(
        `
        <div>
          <p><strong>作业标题:</strong> ${response.data.title}</p>
          <p><strong>创建教师:</strong> ${response.data.creator_name}</p>
          <p><strong>所属班级:</strong> ${response.data.class_name}</p>
          <p><strong>题目数量:</strong> ${response.data.question_count}</p>
          <p><strong>完成率:</strong> ${response.data.completion_rate}%</p>
          <p><strong>截止时间:</strong> ${formatDate(response.data.due_at)}</p>
          <p><strong>发布状态:</strong> ${response.data.is_published ? '已发布' : '草稿'}</p>
        </div>
        `,
        '作业详情',
        {
          dangerouslyUseHTMLString: true,
          confirmButtonText: '确定'
        }
      )
    }
  } catch (error) {
    ElMessage.error('获取作业详情失败')
  }
}

const viewProgress = async (row) => {
  try {
    const response = await adminApi.getHomeworkProgress(row.id)
    if (response.success) {
      const data = response.data
      const progressInfo = `
        <div>
          <h4>作业进度统计</h4>
          <p><strong>总学生数:</strong> ${data.total_students}</p>
          <p><strong>已完成:</strong> ${data.completed_count} 人</p>
          <p><strong>进行中:</strong> ${data.in_progress_count} 人</p>
          <p><strong>未开始:</strong> ${data.not_started_count} 人</p>
          <p><strong>完成率:</strong> ${data.completion_rate}%</p>
          <p><strong>平均分:</strong> ${data.average_score} 分</p>
        </div>
      `
      ElMessageBox.alert(progressInfo, '作业进度', {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '确定'
      })
    }
  } catch (error) {
    ElMessage.error('获取作业进度失败')
  }
}

const extendDeadline = async (row) => {
  try {
    const { value: dateTime } = await ElMessageBox.prompt(
      '请选择新的截止时间',
      '延期作业',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputType: 'datetime-local'
      }
    )

    if (dateTime) {
      const response = await adminApi.extendHomeworkDeadline(row.id, {
        new_due_date: new Date(dateTime).toISOString(),
        reason: '管理员延期'
      })

      if (response.success) {
        ElMessage.success('作业延期成功')
        loadData()
      } else {
        ElMessage.error(response.message || '延期失败')
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('延期操作失败')
    }
  }
}

const exportReport = async (row) => {
  try {
    const response = await adminApi.exportHomeworkReport(row.id, 'csv')

    // 创建下载链接
    const blob = new Blob([response], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `homework_report_${row.id}_${new Date().getTime()}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('报告导出成功')
  } catch (error) {
    ElMessage.error('导出报告失败')
  }
}

const sendReminder = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要向未完成作业的学生发送提醒吗？`,
      '发送提醒',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await adminApi.sendHomeworkReminder(row.id)
    if (response.success) {
      ElMessage.success(response.message)
    } else {
      ElMessage.error(response.message || '发送提醒失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('发送提醒失败')
    }
  }
}

onMounted(() => {
  loadData()
  loadTeachers()
  loadClasses()
})
</script>

<style scoped>
.admin-homeworks {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.filters {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 4px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>