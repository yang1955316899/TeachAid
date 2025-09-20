<template>
  <div>
    <a-card title="班级管理" style="margin-bottom: 16px">
      <template #extra>
        <a-button type="primary" @click="showCreateModal = true">
          创建班级
        </a-button>
      </template>
      
      <!-- 搜索区域 -->
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="6">
          <a-input
            v-model:value="searchParams.keyword"
            placeholder="搜索班级名称"
            @pressEnter="handleSearch"
          />
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="searchParams.grade"
            placeholder="年级"
            allow-clear
            @change="handleSearch"
            :loading="gradeLoading"
          >
            <a-select-option v-for="grade in gradeOptions" :key="grade.value" :value="grade.value">
              {{ grade.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button type="primary" @click="handleSearch">搜索</a-button>
          <a-button style="margin-left: 8px" @click="resetSearch">重置</a-button>
        </a-col>
      </a-row>
      
      <a-table
        :columns="columns"
        :data-source="classes"
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
              <a-button size="small" @click="manageTeaching(record)">授课管理</a-button>
              <a-button size="small" @click="manageStudents(record)">管理学生</a-button>
              <a-button size="small" @click="viewStatistics(record)">查看统计</a-button>
              <a-button size="small" @click="editClass(record)">编辑</a-button>
              <a-popconfirm
                title="确定要删除这个班级吗？"
                @confirm="deleteClass(record)"
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

    <!-- 创建/编辑班级模态框 -->
    <a-modal
      v-model:open="showCreateModal"
      :title="editingClass ? '编辑班级' : '创建班级'"
      width="600px"
      @ok="handleCreate"
      :okButtonProps="{ loading: loading }"
    >
      <a-form layout="vertical" :model="form">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="班级名称" required>
              <a-input v-model:value="form.name" placeholder="请输入班级名称" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="年级" required>
              <a-select v-model:value="form.grade_id" placeholder="请选择年级" :loading="gradeLoading">
                <a-select-option v-for="grade in gradeOptions" :key="grade.value" :value="grade.value">
                  {{ grade.label }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="班级容量">
              <a-input-number
                v-model:value="form.max_students"
                :min="1"
                :max="100"
                style="width: 100%"
                placeholder="请输入班级容量"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-form-item label="班级描述">
          <a-textarea
            v-model:value="form.description"
            placeholder="请输入班级描述"
            :rows="3"
            show-count
            :maxlength="500"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 学生管理模态框 -->
    <a-modal
      v-model:open="showStudentModal"
      title="学生管理"
      width="800px"
      :footer="null"
    >
      <div v-if="currentClass">
        <a-row :gutter="16" style="margin-bottom: 16px">
          <a-col :span="12">
            <a-descriptions title="班级信息" bordered>
              <a-descriptions-item label="班级名称">{{ currentClass.name }}</a-descriptions-item>
              <a-descriptions-item label="年级">{{ currentClass.grade }}</a-descriptions-item>
              <a-descriptions-item label="学科">{{ currentClass.subject }}</a-descriptions-item>
              <a-descriptions-item label="当前学生数">{{ students.length }}</a-descriptions-item>
            </a-descriptions>
          </a-col>
          <a-col :span="12">
            <a-card title="添加学生" size="small">
              <a-form layout="vertical" :model="studentForm">
                <a-row :gutter="8">
                  <a-col :span="12">
                    <a-form-item label="学生姓名">
                      <a-input v-model:value="studentForm.name" placeholder="学生姓名" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="学号">
                      <a-input v-model:value="studentForm.studentId" placeholder="学号" />
                    </a-form-item>
                  </a-col>
                </a-row>
                <a-form-item>
                  <a-button type="primary" @click="addStudent" :loading="addingStudent">
                    添加学生
                  </a-button>
                </a-form-item>
              </a-form>
            </a-card>
          </a-col>
        </a-row>
        
        <a-table
          :columns="studentColumns"
          :data-source="students"
          :loading="studentsLoading"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action'">
              <a-popconfirm
                title="确定要移除这个学生吗？"
                @confirm="removeStudent(record)"
                ok-text="确定"
                cancel-text="取消"
              >
                <a-button size="small" danger>移除</a-button>
              </a-popconfirm>
            </template>
          </template>
        </a-table>
      </div>
    </a-modal>

    <!-- 班级统计模态框 -->
    <a-modal
      v-model:open="showStatisticsModal"
      title="班级统计"
      width="600px"
      :footer="null"
    >
      <div v-if="currentClass">
        <a-descriptions title="基本信息" bordered>
          <a-descriptions-item label="班级名称">{{ currentClass.name }}</a-descriptions-item>
          <a-descriptions-item label="年级">{{ currentClass.grade }}</a-descriptions-item>
          <a-descriptions-item label="学科">{{ currentClass.subject }}</a-descriptions-item>
          <a-descriptions-item label="学生总数">{{ statistics.totalStudents || 0 }}</a-descriptions-item>
          <a-descriptions-item label="作业总数">{{ statistics.totalHomeworks || 0 }}</a-descriptions-item>
          <a-descriptions-item label="平均完成率">{{ statistics.averageCompletionRate || 0 }}%</a-descriptions-item>
        </a-descriptions>
        
        <a-row :gutter="16" style="margin-top: 16px">
          <a-col :span="12">
            <a-card title="完成率分布" size="small">
              <a-progress 
                :percent="statistics.highCompletionRate || 0" 
                status="success"
                :show-info="true"
              >
                高完成率 (>80%)
              </a-progress>
              <a-progress 
                :percent="statistics.mediumCompletionRate || 0" 
                status="normal"
                :show-info="true"
                style="margin-top: 8px"
              >
                中完成率 (50-80%)
              </a-progress>
              <a-progress 
                :percent="statistics.lowCompletionRate || 0" 
                status="exception"
                :show-info="true"
                style="margin-top: 8px"
              >
                低完成率 (<50%)
              </a-progress>
            </a-card>
          </a-col>
          <a-col :span="12">
            <a-card title="活跃度统计" size="small">
              <a-statistic title="活跃学生" :value="statistics.activeStudents || 0" />
              <a-statistic title="不活跃学生" :value="statistics.inactiveStudents || 0" style="margin-top: 16px" />
              <a-statistic title="平均登录次数" :value="statistics.averageLoginCount || 0" style="margin-top: 16px" />
            </a-card>
          </a-col>
        </a-row>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { useClassStore } from '@/stores/class'
import { storeToRefs } from 'pinia'
import { eduApi } from '@/api/edu'
import { message } from 'ant-design-vue'

export default {
  name: 'ClassManage',
  data() {
    return {
      showCreateModal: false,
      showStudentModal: false,
      showStatisticsModal: false,
      editingClass: null,
      currentClass: null,
      students: [],
      studentsLoading: false,
      addingStudent: false,
      statistics: {},
      form: {
        name: '',
        grade_id: '',
        max_students: 50,
        description: ''
      },
      studentForm: {
        name: '',
        studentId: ''
      },
      searchParams: {
        keyword: '',
        grade: ''
      },
      // 动态选项
      gradeOptions: [],
      gradeLoading: false,
      columns: [
        {
          title: '班级名称',
          dataIndex: 'name',
          key: 'name'
        },
        {
          title: '年级',
          dataIndex: 'grade_name',
          key: 'grade_name'
        },
        {
          title: '授课教师',
          key: 'teachers',
          customRender: ({ record }) => {
            if (!record.teachers || record.teachers.length === 0) {
              return '暂无授课教师'
            }
            return record.teachers.map(t => `${t.teacher_name}(${t.subject_name || '未知学科'})`).join(', ')
          }
        },
        {
          title: '学生人数',
          dataIndex: 'student_count',
          key: 'studentCount'
        },
        {
          title: '容量',
          dataIndex: 'capacity',
          key: 'capacity'
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
      studentColumns: [
        {
          title: '学生姓名',
          dataIndex: 'name',
          key: 'name'
        },
        {
          title: '学号',
          dataIndex: 'student_id',
          key: 'studentId'
        },
        {
          title: '加入时间',
          dataIndex: 'joined_at',
          key: 'joinedAt'
        },
        {
          title: '操作',
          key: 'action'
        }
      ]
    }
  },
  computed: {
    classStore() {
      return useClassStore()
    }
  },
  setup() {
    const classStore = useClassStore()
    const { classes, loading, pagination } = storeToRefs(classStore)
    
    return {
      classes,
      loading,
      pagination
    }
  },
  mounted() {
    this.loadClasses()
    this.loadGrades()
  },
  methods: {
    async loadClasses() {
      try {
        await this.classStore.fetchClasses({
          page: this.pagination.current,
          size: this.pagination.pageSize,
          ...this.searchParams
        })
      } catch (error) {
        console.error('加载班级失败:', error)
      }
    },

    async loadGrades() {
      this.gradeLoading = true
      try {
        const response = await eduApi.getGrades()
        if (response.success) {
          this.gradeOptions = (response.data.items || []).map(item => ({
            label: item.name,
            value: item.id
          }))
        }
      } catch (error) {
        console.error('加载年级列表失败:', error)
        message.error('加载年级列表失败')
      } finally {
        this.gradeLoading = false
      }
    },

    async handleSearch() {
      this.pagination.current = 1
      await this.loadClasses()
    },

    resetSearch() {
      this.searchParams = {
        keyword: '',
        grade: ''
      }
      this.handleSearch()
    },

    async handlePaginationChange(page, pageSize) {
      this.pagination.current = page
      this.pagination.pageSize = pageSize
      await this.loadClasses()
    },

    async handleCreate() {
      if (!this.form.name || !this.form.grade_id) {
        this.$message.warning('请填写必填字段')
        return
      }

      try {
        if (this.editingClass) {
          await this.classStore.updateClass(this.editingClass.id, this.form)
        } else {
          await this.classStore.createClass(this.form)
        }
        this.showCreateModal = false
        this.resetForm()
        await this.loadClasses()
        this.$message.success('班级保存成功')
      } catch (error) {
        console.error('保存班级失败:', error)
        this.$message.error('保存班级失败')
      }
    },

    editClass(record) {
      this.editingClass = record
      this.form = {
        name: record.name,
        grade_id: record.grade_id,
        max_students: record.max_students || 50,
        description: record.description || ''
      }
      this.showCreateModal = true
    },

    async deleteClass(record) {
      try {
        await this.classStore.deleteClass(record.id)
      } catch (error) {
        console.error('删除班级失败:', error)
      }
    },

    async manageStudents(record) {
      this.currentClass = record
      this.showStudentModal = true
      await this.loadStudents(record.id)
    },

    async loadStudents(classId) {
      this.studentsLoading = true
      try {
        const response = await this.classStore.fetchClassStudents(classId)
        this.students = response.students || []
      } catch (error) {
        console.error('加载学生失败:', error)
      } finally {
        this.studentsLoading = false
      }
    },

    async addStudent() {
      if (!this.studentForm.name || !this.studentForm.studentId) {
        this.$message.warning('请填写学生信息')
        return
      }

      this.addingStudent = true
      try {
        await this.classStore.addStudentToClass(this.currentClass.id, this.studentForm)
        this.studentForm = { name: '', studentId: '' }
        await this.loadStudents(this.currentClass.id)
      } catch (error) {
        console.error('添加学生失败:', error)
      } finally {
        this.addingStudent = false
      }
    },

    async removeStudent(record) {
      try {
        await this.classStore.removeStudentFromClass(this.currentClass.id, record.id)
        await this.loadStudents(this.currentClass.id)
      } catch (error) {
        console.error('移除学生失败:', error)
      }
    },

    viewStatistics(record) {
      this.currentClass = record
      this.showStatisticsModal = true
      // 调用后端统计API
      import('@/api/analytics').then(async ({ analyticsApi }) => {
        try {
          const res = await analyticsApi.getClassOverview(record.id)
          if (res.success) {
            this.statistics = res.data || {}
          } else {
            this.$message.error('获取班级统计失败')
          }
        } catch (e) {
          console.error('获取班级统计失败:', e)
          this.$message.error('获取班级统计失败')
        }
      })
    },

    resetForm() {
      this.form = {
        name: '',
        grade_id: '',
        max_students: 50,
        description: ''
      }
      this.editingClass = null
    },

    // 新增授课管理方法
    async manageTeaching(record) {
      try {
        // 跳转到授课关系管理页面，并传递班级ID作为筛选条件
        this.$router.push({
          path: '/teacher/teaching',
          query: { classId: record.id, className: record.name }
        })
      } catch (error) {
        console.error('跳转授课管理失败:', error)
        this.$message.error('无法打开授课管理页面')
      }
    }
  }
}
</script>
