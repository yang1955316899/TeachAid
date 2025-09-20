<template>
  <div class="admin-create-class">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>创建班级</h1>
      <p>添加新的班级到系统中</p>
    </div>

    <!-- 创建表单 -->
    <el-card>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        style="max-width: 600px"
      >
        <el-form-item label="班级名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入班级名称"
            :prefix-icon="School"
          />
          <div class="form-tip">班级名称应该简洁明了，便于识别</div>
        </el-form-item>

        <el-form-item label="班级描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入班级描述（可选）"
          />
          <div class="form-tip">可以描述班级的特点、学习重点等信息</div>
        </el-form-item>

        <el-form-item label="所属年级" prop="grade_id">
          <el-select
            v-model="form.grade_id"
            placeholder="请选择年级"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="grade in grades"
              :key="grade.id"
              :label="grade.name"
              :value="grade.id"
            />
          </el-select>
          <div class="form-tip">选择班级所属的年级</div>
        </el-form-item>

        <el-form-item label="所属机构" prop="organization_id">
          <el-select
            v-model="form.organization_id"
            placeholder="请选择所属机构（可选）"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="org in organizations"
              :key="org.organization_id"
              :label="org.name"
              :value="org.organization_id"
            />
          </el-select>
          <div class="form-tip">如不选择，班级将属于默认机构</div>
        </el-form-item>

        <el-form-item label="最大学生数" prop="max_students">
          <el-input-number
            v-model="form.max_students"
            :min="1"
            :max="200"
            :step="1"
            style="width: 200px"
          />
          <div class="form-tip">设置班级可容纳的最大学生数量</div>
        </el-form-item>

        <el-divider content-position="left">班级设置</el-divider>

        <el-form-item label="班级状态">
          <el-radio-group v-model="form.is_active">
            <el-radio :label="true">启用</el-radio>
            <el-radio :label="false">禁用</el-radio>
          </el-radio-group>
          <div class="form-tip">创建后是否立即启用班级</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            创建班级
          </el-button>
          <el-button @click="handleCancel">
            取消
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 预览卡片 -->
    <el-card v-if="form.name" class="preview-card">
      <template #header>
        <div class="card-header">
          <span>班级预览</span>
        </div>
      </template>
      <div class="preview-content">
        <div class="preview-item">
          <strong>班级名称：</strong>{{ form.name }}
        </div>
        <div v-if="form.description" class="preview-item">
          <strong>班级描述：</strong>{{ form.description }}
        </div>
        <div v-if="selectedGradeName" class="preview-item">
          <strong>所属年级：</strong>{{ selectedGradeName }}
        </div>
        <div v-if="selectedOrgName" class="preview-item">
          <strong>所属机构：</strong>{{ selectedOrgName }}
        </div>
        <div class="preview-item">
          <strong>最大学生数：</strong>{{ form.max_students }}
        </div>
        <div class="preview-item">
          <strong>状态：</strong>
          <el-tag :type="form.is_active ? 'success' : 'danger'" size="small">
            {{ form.is_active ? '启用' : '禁用' }}
          </el-tag>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'
import { School } from '@element-plus/icons-vue'

export default {
  name: 'AdminCreateClass',
  components: {
    School
  },
  setup() {
    const router = useRouter()
    const adminStore = useAdminStore()

    const formRef = ref(null)
    const loading = ref(false)
    const grades = ref([])
    const organizations = ref([])

    const form = reactive({
      name: '',
      description: '',
      grade_id: '',
      organization_id: '',
      max_students: 50,
      is_active: true
    })

    const rules = {
      name: [
        { required: true, message: '请输入班级名称', trigger: 'blur' },
        { min: 2, max: 100, message: '班级名称长度在 2 到 100 个字符', trigger: 'blur' }
      ],
      max_students: [
        { required: true, message: '请设置最大学生数', trigger: 'blur' },
        { type: 'number', min: 1, max: 200, message: '最大学生数必须在 1 到 200 之间', trigger: 'change' }
      ]
    }

    // 计算属性
    const selectedGradeName = computed(() => {
      const grade = grades.value.find(g => g.id === form.grade_id)
      return grade ? grade.name : ''
    })

    const selectedOrgName = computed(() => {
      const org = organizations.value.find(o => o.organization_id === form.organization_id)
      return org ? org.name : ''
    })

    const loadGrades = async () => {
      // 模拟年级数据
      grades.value = [
        { id: '1', name: '一年级' },
        { id: '2', name: '二年级' },
        { id: '3', name: '三年级' },
        { id: '4', name: '四年级' },
        { id: '5', name: '五年级' },
        { id: '6', name: '六年级' },
        { id: '7', name: '初一' },
        { id: '8', name: '初二' },
        { id: '9', name: '初三' },
        { id: '10', name: '高一' },
        { id: '11', name: '高二' },
        { id: '12', name: '高三' }
      ]
    }

    const loadOrganizations = async () => {
      // 模拟机构数据
      organizations.value = [
        { organization_id: '1', name: '总部' },
        { organization_id: '2', name: '北京分部' },
        { organization_id: '3', name: '上海分部' },
        { organization_id: '4', name: '广州分部' },
        { organization_id: '5', name: '深圳分部' }
      ]
    }

    const handleSubmit = async () => {
      try {
        // 表单验证
        const valid = await formRef.value.validate()
        if (!valid) return

        loading.value = true

        // 准备提交数据
        const submitData = {
          name: form.name,
          description: form.description || null,
          grade_id: form.grade_id || null,
          organization_id: form.organization_id || null,
          max_students: form.max_students
        }

        // 调用API创建班级
        await adminStore.createClass(submitData)

        ElMessage.success('班级创建成功')

        // 返回班级列表页面
        router.push('/admin/classes')

      } catch (error) {
        console.error('创建班级失败:', error)
        ElMessage.error(error.response?.data?.message || '创建班级失败')
      } finally {
        loading.value = false
      }
    }

    const handleCancel = () => {
      router.back()
    }

    onMounted(() => {
      loadGrades()
      loadOrganizations()
    })

    return {
      formRef,
      form,
      rules,
      loading,
      grades,
      organizations,
      selectedGradeName,
      selectedOrgName,
      handleSubmit,
      handleCancel
    }
  }
}
</script>

<style scoped>
.admin-create-class {
  padding: 0;
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 20px;
}

.page-header {
  grid-column: 1 / -1;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.preview-card {
  height: fit-content;
  position: sticky;
  top: 20px;
}

.preview-content {
  padding: 0;
}

.preview-item {
  margin-bottom: 12px;
  line-height: 1.6;
}

.preview-item:last-child {
  margin-bottom: 0;
}

.preview-item strong {
  color: #303133;
  margin-right: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-card__body) {
  padding: 24px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-divider__text) {
  background-color: #f5f7fa;
  color: #909399;
  font-weight: 500;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .admin-create-class {
    grid-template-columns: 1fr;
  }

  .preview-card {
    position: static;
  }
}
</style>