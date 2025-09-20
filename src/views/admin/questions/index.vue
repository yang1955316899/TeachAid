<template>
  <div class="admin-questions">
    <div class="header">
      <h2>题目管理</h2>
    </div>

    <div class="filters">
      <el-form :model="filters" layout="inline">
        <el-form-item label="学科">
          <el-select v-model="filters.subject" placeholder="选择学科" clearable>
            <el-option label="数学" value="math" />
            <el-option label="语文" value="chinese" />
            <el-option label="英语" value="english" />
            <el-option label="物理" value="physics" />
            <el-option label="化学" value="chemistry" />
          </el-select>
        </el-form-item>
        <el-form-item label="题型">
          <el-select v-model="filters.questionType" placeholder="选择题型" clearable>
            <el-option label="选择题" value="choice" />
            <el-option label="填空题" value="blank" />
            <el-option label="解答题" value="answer" />
            <el-option label="计算题" value="calculation" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="filters.difficulty" placeholder="选择难度" clearable>
            <el-option label="简单" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="困难" value="hard" />
          </el-select>
        </el-form-item>
        <el-form-item label="创建者">
          <el-select v-model="filters.creatorId" placeholder="选择创建者" clearable>
            <el-option
              v-for="teacher in teachers"
              :key="teacher.id"
              :label="teacher.name"
              :value="teacher.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-table :data="questions" v-loading="loading">
      <el-table-column prop="title" label="题目标题" width="200" show-overflow-tooltip />
      <el-table-column prop="subject" label="学科" width="80" />
      <el-table-column prop="questionType" label="题型" width="100" />
      <el-table-column prop="difficulty" label="难度" width="80">
        <template #default="{ row }">
          <el-tag :type="getDifficultyType(row.difficulty)">
            {{ getDifficultyText(row.difficulty) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="creatorName" label="创建者" width="100" />
      <el-table-column prop="qualityScore" label="质量分数" width="100">
        <template #default="{ row }">
          <el-rate v-model="row.qualityScore" disabled max="5" />
        </template>
      </el-table-column>
      <el-table-column prop="usageCount" label="使用次数" width="100" />
      <el-table-column prop="createdAt" label="创建时间" width="150">
        <template #default="{ row }">
          {{ formatDate(row.createdAt) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.isActive ? 'success' : 'info'">
            {{ row.isActive ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewQuestion(row)">查看</el-button>
          <el-button size="small" type="primary" @click="editQuestion(row)">编辑</el-button>
          <el-dropdown>
            <el-button size="small">
              更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="toggleStatus(row)">
                  {{ row.isActive ? '禁用' : '启用' }}
                </el-dropdown-item>
                <el-dropdown-item @click="rewriteAnswer(row)">重新改写</el-dropdown-item>
                <el-dropdown-item @click="viewUsage(row)">使用统计</el-dropdown-item>
                <el-dropdown-item @click="deleteQuestion(row)" divided>删除</el-dropdown-item>
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
const questions = ref([])
const teachers = ref([])

const filters = reactive({
  subject: '',
  questionType: '',
  difficulty: '',
  creatorId: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const getDifficultyType = (difficulty) => {
  const typeMap = {
    'easy': 'success',
    'medium': 'warning',
    'hard': 'danger'
  }
  return typeMap[difficulty] || 'info'
}

const getDifficultyText = (difficulty) => {
  const textMap = {
    'easy': '简单',
    'medium': '中等',
    'hard': '困难'
  }
  return textMap[difficulty] || '未知'
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    // 模拟数据
    questions.value = [
      {
        id: '1',
        title: '一元二次方程的解法',
        subject: '数学',
        questionType: '解答题',
        difficulty: 'medium',
        creatorName: '张老师',
        qualityScore: 4,
        usageCount: 15,
        createdAt: '2024-09-01',
        isActive: true
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
    subject: '',
    questionType: '',
    difficulty: '',
    creatorId: ''
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

const viewQuestion = (row) => {
  ElMessage.info('查看题目功能待实现')
}

const editQuestion = (row) => {
  ElMessage.info('编辑题目功能待实现')
}

const toggleStatus = (row) => {
  row.isActive = !row.isActive
  ElMessage.success(`题目已${row.isActive ? '启用' : '禁用'}`)
}

const rewriteAnswer = (row) => {
  ElMessage.info('重新改写功能待实现')
}

const viewUsage = (row) => {
  ElMessage.info('使用统计功能待实现')
}

const deleteQuestion = (row) => {
  ElMessage.info('删除题目功能待实现')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.admin-questions {
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