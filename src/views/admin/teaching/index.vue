<template>
  <div class="admin-teaching-assignments">
    <div class="header">
      <h2>授课安排管理</h2>
      <el-button type="primary" @click="createAssignment">
        <el-icon><Plus /></el-icon>
        新建授课安排
      </el-button>
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
        <el-form-item label="学期">
          <el-select v-model="filters.semester" placeholder="选择学期" clearable>
            <el-option label="2024春季" value="2024-spring" />
            <el-option label="2024秋季" value="2024-fall" />
            <el-option label="2025春季" value="2025-spring" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-table :data="assignments" v-loading="loading">
      <el-table-column prop="teacherName" label="教师" width="120" />
      <el-table-column prop="className" label="班级" width="150" />
      <el-table-column prop="subject" label="学科" width="100" />
      <el-table-column prop="semester" label="学期" width="120" />
      <el-table-column prop="schedule" label="授课时间" width="200">
        <template #default="{ row }">
          <div v-for="schedule in row.schedules" :key="schedule.id" class="schedule-item">
            {{ schedule.dayOfWeek }} {{ schedule.timeSlot }}
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.createdAt) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="editAssignment(row)">编辑</el-button>
          <el-button size="small" type="info" @click="viewDetails(row)">详情</el-button>
          <el-popconfirm
            title="确定要删除这个授课安排吗？"
            @confirm="deleteAssignment(row)"
          >
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
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

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑授课安排' : '新建授课安排'"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="教师" prop="teacherId">
          <el-select v-model="form.teacherId" placeholder="选择教师">
            <el-option
              v-for="teacher in teachers"
              :key="teacher.id"
              :label="teacher.name"
              :value="teacher.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="班级" prop="classId">
          <el-select v-model="form.classId" placeholder="选择班级">
            <el-option
              v-for="cls in classes"
              :key="cls.id"
              :label="cls.name"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="学科" prop="subject">
          <el-input v-model="form.subject" placeholder="请输入学科" />
        </el-form-item>
        <el-form-item label="学期" prop="semester">
          <el-select v-model="form.semester" placeholder="选择学期">
            <el-option label="2024春季" value="2024-spring" />
            <el-option label="2024秋季" value="2024-fall" />
            <el-option label="2025春季" value="2025-spring" />
          </el-select>
        </el-form-item>
        <el-form-item label="授课时间">
          <div v-for="(schedule, index) in form.schedules" :key="index" class="schedule-form-item">
            <el-select v-model="schedule.dayOfWeek" placeholder="选择星期">
              <el-option label="周一" value="monday" />
              <el-option label="周二" value="tuesday" />
              <el-option label="周三" value="wednesday" />
              <el-option label="周四" value="thursday" />
              <el-option label="周五" value="friday" />
              <el-option label="周六" value="saturday" />
              <el-option label="周日" value="sunday" />
            </el-select>
            <el-time-picker
              v-model="schedule.timeSlot"
              is-range
              format="HH:mm"
              placeholder="选择时间段"
            />
            <el-button
              type="danger"
              size="small"
              @click="removeSchedule(index)"
              v-if="form.schedules.length > 1"
            >
              删除
            </el-button>
          </div>
          <el-button type="primary" size="small" @click="addSchedule">
            添加时间段
          </el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAssignment" :loading="saving">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

// 数据状态
const loading = ref(false)
const saving = ref(false)
const assignments = ref([])
const teachers = ref([])
const classes = ref([])

// 筛选条件
const filters = reactive({
  teacherId: '',
  classId: '',
  semester: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()

// 表单数据
const form = reactive({
  id: '',
  teacherId: '',
  classId: '',
  subject: '',
  semester: '',
  schedules: [{
    dayOfWeek: '',
    timeSlot: []
  }]
})

// 表单验证规则
const rules = {
  teacherId: [{ required: true, message: '请选择教师', trigger: 'change' }],
  classId: [{ required: true, message: '请选择班级', trigger: 'change' }],
  subject: [{ required: true, message: '请输入学科', trigger: 'blur' }],
  semester: [{ required: true, message: '请选择学期', trigger: 'change' }]
}

// 状态相关方法
const getStatusType = (status) => {
  const typeMap = {
    'active': 'success',
    'inactive': 'info',
    'pending': 'warning',
    'cancelled': 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'active': '进行中',
    'inactive': '已结束',
    'pending': '待开始',
    'cancelled': '已取消'
  }
  return textMap[status] || '未知'
}

const formatDate = (date) => {
  return new Date(date).toLocaleString('zh-CN')
}

// 初始化数据
const initData = async () => {
  try {
    loading.value = true
    // TODO: 调用实际API
    await loadTeachers()
    await loadClasses()
    await loadAssignments()
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const loadTeachers = async () => {
  // 模拟数据
  teachers.value = [
    { id: '1', name: '张老师' },
    { id: '2', name: '李老师' },
    { id: '3', name: '王老师' }
  ]
}

const loadClasses = async () => {
  // 模拟数据
  classes.value = [
    { id: '1', name: '初一(1)班' },
    { id: '2', name: '初一(2)班' },
    { id: '3', name: '初二(1)班' }
  ]
}

const loadAssignments = async () => {
  // 模拟数据
  assignments.value = [
    {
      id: '1',
      teacherName: '张老师',
      className: '初一(1)班',
      subject: '数学',
      semester: '2024-fall',
      schedules: [
        { id: '1', dayOfWeek: '周一', timeSlot: '08:00-09:30' },
        { id: '2', dayOfWeek: '周三', timeSlot: '10:00-11:30' }
      ],
      status: 'active',
      createdAt: '2024-09-01T08:00:00'
    }
  ]
  pagination.total = 1
}

// 搜索和筛选
const search = () => {
  pagination.page = 1
  loadAssignments()
}

const resetFilters = () => {
  Object.assign(filters, {
    teacherId: '',
    classId: '',
    semester: ''
  })
  search()
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.size = size
  loadAssignments()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  loadAssignments()
}

// 表单操作
const createAssignment = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const editAssignment = (row) => {
  isEdit.value = true
  Object.assign(form, row)
  dialogVisible.value = true
}

const resetForm = () => {
  Object.assign(form, {
    id: '',
    teacherId: '',
    classId: '',
    subject: '',
    semester: '',
    schedules: [{
      dayOfWeek: '',
      timeSlot: []
    }]
  })
  formRef.value?.resetFields()
}

const addSchedule = () => {
  form.schedules.push({
    dayOfWeek: '',
    timeSlot: []
  })
}

const removeSchedule = (index) => {
  form.schedules.splice(index, 1)
}

const saveAssignment = async () => {
  try {
    await formRef.value.validate()
    saving.value = true

    // TODO: 调用实际API保存数据
    await new Promise(resolve => setTimeout(resolve, 1000))

    ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    loadAssignments()
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    saving.value = false
  }
}

const viewDetails = (row) => {
  ElMessageBox.alert(`授课安排详情: ${row.teacherName} - ${row.className}`, '详情', {
    confirmButtonText: '确定'
  })
}

const deleteAssignment = async (row) => {
  try {
    // TODO: 调用实际API删除
    await new Promise(resolve => setTimeout(resolve, 500))

    ElMessage.success('删除成功')
    loadAssignments()
  } catch (error) {
    ElMessage.error('删除失败')
    console.error(error)
  }
}

onMounted(() => {
  initData()
})
</script>

<style scoped>
.admin-teaching-assignments {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filters {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 4px;
}

.schedule-item {
  margin-bottom: 5px;
}

.schedule-form-item {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>