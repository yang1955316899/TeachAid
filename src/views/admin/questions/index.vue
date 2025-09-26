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
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import adminApi from '@/api/admin'

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

const getQuestionTypeText = (type) => {
  const typeMap = {
    'choice': '选择题',
    'blank': '填空题',
    'answer': '解答题',
    'calculation': '计算题'
  }
  return typeMap[type] || type
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      subject: filters.subject || undefined,
      question_type: filters.questionType || undefined,
      difficulty: filters.difficulty || undefined,
      creator_id: filters.creatorId || undefined
    }

    const response = await adminApi.getQuestions(params)

    if (response.data && response.data.items) {
      questions.value = response.data.items.map(item => ({
        id: item.id,
        title: item.title,
        subject: item.subject,
        questionType: item.question_type,
        difficulty: item.difficulty,
        creatorName: item.creator_name || '未知',
        qualityScore: item.quality_score || 0,
        usageCount: 0, // 后端暂无此字段
        createdAt: item.created_time,
        isActive: item.is_active,
        isPublic: item.is_public,
        gradeLevel: item.grade_level,
        knowledgePoints: item.knowledge_points,
        tags: item.tags
      }))
      pagination.total = response.data.total || 0
    } else {
      questions.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('获取题目列表失败:', error)
    ElMessage.error('获取题目列表失败')
    questions.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

const loadTeachers = async () => {
  try {
    const response = await adminApi.getUsers({ role: 'teacher', page: 1, size: 100 })
    if (response.data && response.data.items) {
      teachers.value = response.data.items.map(item => ({
        id: item.id,
        name: item.user_full_name || item.username
      }))
    }
  } catch (error) {
    console.error('获取教师列表失败:', error)
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

const viewQuestion = async (row) => {
  try {
    const response = await adminApi.getQuestionDetail(row.id)
    if (response.data) {
      ElMessageBox.alert(
        `<div style="max-height: 400px; overflow-y: auto;">
          <p><strong>标题:</strong> ${response.data.title || '无标题'}</p>
          <p><strong>学科:</strong> ${response.data.subject}</p>
          <p><strong>题型:</strong> ${getQuestionTypeText(response.data.question_type)}</p>
          <p><strong>难度:</strong> ${getDifficultyText(response.data.difficulty)}</p>
          <p><strong>年级:</strong> ${response.data.grade_level || '未设置'}</p>
          <p><strong>创建者:</strong> ${response.data.creator_name || '未知'}</p>
          <p><strong>质量分数:</strong> ${response.data.quality_score || 0}</p>
          <p><strong>知识点:</strong> ${response.data.knowledge_points ? response.data.knowledge_points.join(', ') : '无'}</p>
          <p><strong>标签:</strong> ${response.data.tags ? response.data.tags.join(', ') : '无'}</p>
          <p><strong>内容:</strong></p>
          <div style="border: 1px solid #ddd; padding: 10px; background: #f9f9f9; white-space: pre-wrap;">${response.data.content || '无内容'}</div>
          ${response.data.original_answer ? `<p><strong>原始答案:</strong></p><div style="border: 1px solid #ddd; padding: 10px; background: #f0f9ff; white-space: pre-wrap;">${response.data.original_answer}</div>` : ''}
          ${response.data.rewritten_answer ? `<p><strong>改写答案:</strong></p><div style="border: 1px solid #ddd; padding: 10px; background: #f0f9f0; white-space: pre-wrap;">${response.data.rewritten_answer}</div>` : ''}
        </div>`,
        '题目详情',
        {
          dangerouslyUseHTMLString: true,
          customClass: 'question-detail-dialog'
        }
      )
    }
  } catch (error) {
    console.error('获取题目详情失败:', error)
    ElMessage.error('获取题目详情失败')
  }
}

const editQuestion = (row) => {
  ElMessage.info('编辑题目功能待实现')
}

const toggleStatus = async (row) => {
  try {
    await adminApi.updateQuestionStatus(row.id, !row.isActive)
    row.isActive = !row.isActive
    ElMessage.success(`题目已${row.isActive ? '启用' : '禁用'}`)
  } catch (error) {
    console.error('更新题目状态失败:', error)
    ElMessage.error('更新题目状态失败')
  }
}

const rewriteAnswer = (row) => {
  ElMessage.info('重新改写功能待实现')
}

const viewUsage = (row) => {
  ElMessage.info('使用统计功能待实现')
}

const deleteQuestion = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除题目"${row.title}"吗？此操作不可恢复。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )

    await adminApi.deleteQuestion(row.id)
    ElMessage.success('题目删除成功')
    loadData() // 重新加载数据
  } catch (error) {
    if (error === 'cancel') {
      return
    }
    console.error('删除题目失败:', error)
    ElMessage.error(error.response?.data?.detail || '删除题目失败')
  }
}

onMounted(() => {
  loadData()
  loadTeachers()
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

<style>
.question-detail-dialog {
  width: 80%;
  max-width: 900px;
}

.question-detail-dialog .el-message-box__content {
  max-height: 70vh;
  overflow-y: auto;
}

.question-detail-dialog .el-message-box__message {
  line-height: 1.6;
}

.question-detail-dialog p {
  margin: 8px 0;
}

.question-detail-dialog strong {
  color: #409eff;
  font-weight: 600;
}

.question-detail-dialog div[style*="border"] {
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  margin: 8px 0;
}
</style>