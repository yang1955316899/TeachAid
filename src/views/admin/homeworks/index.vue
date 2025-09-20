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
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'

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
    // 模拟数据
    homeworks.value = [
      {
        id: '1',
        title: '数学练习题第一套',
        teacherName: '张老师',
        className: '初一(1)班',
        questionCount: 10,
        submissionCount: 25,
        totalStudents: 30,
        dueDate: '2024-09-25T23:59:59',
        status: 'active'
      }
    ]
    pagination.total = 1
  } finally {
    loading.value = false
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

const viewDetails = (row) => {
  ElMessage.info('查看作业详情功能待实现')
}

const viewProgress = (row) => {
  ElMessage.info('查看作业进度功能待实现')
}

const extendDeadline = (row) => {
  ElMessage.info('延期功能待实现')
}

const exportReport = (row) => {
  ElMessage.info('导出报告功能待实现')
}

const sendReminder = (row) => {
  ElMessage.info('发送提醒功能待实现')
}

onMounted(() => {
  loadData()
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