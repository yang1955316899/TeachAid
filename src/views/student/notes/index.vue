<template>
  <div class="notes-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          新建笔记
        </a-button>
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索笔记..."
          style="width: 300px"
          @search="searchNotes"
        />
        <a-select v-model:value="selectedSubject" placeholder="选择科目" style="width: 150px" @change="filterNotes">
          <a-select-option value="">全部科目</a-select-option>
          <a-select-option value="数学">数学</a-select-option>
          <a-select-option value="语文">语文</a-select-option>
          <a-select-option value="英语">英语</a-select-option>
          <a-select-option value="物理">物理</a-select-option>
          <a-select-option value="化学">化学</a-select-option>
        </a-select>
      </div>
      <div class="toolbar-right">
        <a-button-group>
          <a-button :type="viewMode === 'grid' ? 'primary' : 'default'" @click="viewMode = 'grid'">
            <AppstoreOutlined />
          </a-button>
          <a-button :type="viewMode === 'list' ? 'primary' : 'default'" @click="viewMode = 'list'">
            <UnorderedListOutlined />
          </a-button>
        </a-button-group>
      </div>
    </div>

    <!-- 笔记列表 -->
    <div v-if="viewMode === 'grid'" class="notes-grid">
      <div
        v-for="note in filteredNotes"
        :key="note.id"
        class="note-card"
        @click="editNote(note)"
      >
        <div class="note-header">
          <div class="note-title">{{ note.title }}</div>
          <div class="note-subject">{{ note.subject }}</div>
        </div>
        <div class="note-content">{{ note.preview }}</div>
        <div class="note-footer">
          <div class="note-date">{{ formatDate(note.updateTime) }}</div>
          <div class="note-actions">
            <a-button type="text" size="small" @click.stop="editNote(note)">
              <EditOutlined />
            </a-button>
            <a-button type="text" size="small" @click.stop="deleteNote(note)">
              <DeleteOutlined />
            </a-button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="notes-list">
      <a-table
        :columns="columns"
        :data-source="filteredNotes"
        :pagination="{ pageSize: 10 }"
        rowKey="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'title'">
            <div class="note-title-cell">
              <div class="note-title">{{ record.title }}</div>
              <div class="note-subject">{{ record.subject }}</div>
            </div>
          </template>
          <template v-if="column.key === 'content'">
            <div class="note-content-cell">{{ record.preview }}</div>
          </template>
          <template v-if="column.key === 'time'">
            <div class="note-time-cell">{{ formatDate(record.updateTime) }}</div>
          </template>
          <template v-if="column.key === 'actions'">
            <div class="note-actions-cell">
              <a-button type="text" size="small" @click="editNote(record)">
                <EditOutlined />
              </a-button>
              <a-button type="text" size="small" @click="deleteNote(record)">
                <DeleteOutlined />
              </a-button>
            </div>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 创建/编辑笔记模态框 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="editingNote ? '编辑笔记' : '新建笔记'"
      @ok="saveNote"
      @cancel="cancelEdit"
      width="800px"
    >
      <a-form :model="noteForm" layout="vertical">
        <a-form-item label="标题" required>
          <a-input v-model:value="noteForm.title" placeholder="请输入笔记标题" />
        </a-form-item>
        <a-form-item label="科目" required>
          <a-select v-model:value="noteForm.subject" placeholder="请选择科目">
            <a-select-option value="数学">数学</a-select-option>
            <a-select-option value="语文">语文</a-select-option>
            <a-select-option value="英语">英语</a-select-option>
            <a-select-option value="物理">物理</a-select-option>
            <a-select-option value="化学">化学</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="内容" required>
          <a-textarea
            v-model:value="noteForm.content"
            placeholder="请输入笔记内容..."
            :rows="8"
            show-count
            :maxlength="2000"
          />
        </a-form-item>
        <a-form-item label="标签">
          <a-select
            v-model:value="noteForm.tags"
            mode="tags"
            placeholder="添加标签"
            style="width: 100%"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import {
  PlusOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  EditOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'

export default {
  name: 'StudentNotes',
  components: {
    PlusOutlined,
    AppstoreOutlined,
    UnorderedListOutlined,
    EditOutlined,
    DeleteOutlined
  },
  data() {
    return {
      viewMode: 'grid',
      searchKeyword: '',
      selectedSubject: '',
      modalVisible: false,
      editingNote: null,
      noteForm: {
        title: '',
        subject: '',
        content: '',
        tags: []
      },
      notes: [
        {
          id: 1,
          title: '二次函数的性质',
          subject: '数学',
          content: '二次函数的一般形式是 f(x) = ax² + bx + c，其中a≠0。\n\n主要性质：\n1. 开口方向：a>0向上，a<0向下\n2. 对称轴：x = -b/(2a)\n3. 顶点坐标：(-b/(2a), f(-b/(2a)))\n4. 增减性：对称轴两侧单调性相反',
          tags: ['函数', '二次函数', '数学'],
          createTime: '2024-01-15T10:30:00',
          updateTime: '2024-01-15T10:30:00'
        },
        {
          id: 2,
          title: '英语语法：时态总结',
          subject: '英语',
          content: '时态是英语语法中的重要概念，包括：\n\n1. 一般现在时：表示经常性动作\n2. 现在进行时：表示正在进行的动作\n3. 一般过去时：表示过去发生的动作\n4. 过去进行时：表示过去某时刻正在进行的动作\n5. 一般将来时：表示将来要发生的动作\n6. 现在完成时：表示过去发生但与现在有关的动作',
          tags: ['时态', '语法', '英语'],
          createTime: '2024-01-14T15:20:00',
          updateTime: '2024-01-14T15:20:00'
        },
        {
          id: 3,
          title: '物理公式：力学部分',
          subject: '物理',
          content: '力学基本公式：\n\n1. 牛顿第二定律：F = ma\n2. 动能公式：Ek = ½mv²\n3. 势能公式：Ep = mgh\n4. 功的公式：W = F·s·cosθ\n5. 功率公式：P = W/t = F·v\n6. 冲量公式：I = F·t = Δp',
          tags: ['力学', '公式', '物理'],
          createTime: '2024-01-13T09:45:00',
          updateTime: '2024-01-13T09:45:00'
        }
      ]
    }
  },
  computed: {
    filteredNotes() {
      let result = this.notes
      
      // 按科目筛选
      if (this.selectedSubject) {
        result = result.filter(note => note.subject === this.selectedSubject)
      }
      
      // 按关键词搜索
      if (this.searchKeyword) {
        result = result.filter(note => 
          note.title.toLowerCase().includes(this.searchKeyword.toLowerCase()) ||
          note.content.toLowerCase().includes(this.searchKeyword.toLowerCase()) ||
          note.tags.some(tag => tag.toLowerCase().includes(this.searchKeyword.toLowerCase()))
        )
      }
      
      // 按更新时间倒序排列
      return result.sort((a, b) => new Date(b.updateTime) - new Date(a.updateTime))
    },
    columns() {
      return [
        {
          title: '标题',
          key: 'title',
          width: 200
        },
        {
          title: '内容',
          key: 'content',
          ellipsis: true
        },
        {
          title: '更新时间',
          key: 'time',
          width: 150
        },
        {
          title: '操作',
          key: 'actions',
          width: 120,
          fixed: 'right'
        }
      ]
    }
  },
  methods: {
    showCreateModal() {
      this.editingNote = null
      this.noteForm = {
        title: '',
        subject: '',
        content: '',
        tags: []
      }
      this.modalVisible = true
    },
    editNote(note) {
      this.editingNote = note
      this.noteForm = {
        title: note.title,
        subject: note.subject,
        content: note.content,
        tags: note.tags
      }
      this.modalVisible = true
    },
    cancelEdit() {
      this.modalVisible = false
      this.editingNote = null
      this.noteForm = {
        title: '',
        subject: '',
        content: '',
        tags: []
      }
    },
    saveNote() {
      if (!this.noteForm.title || !this.noteForm.subject || !this.noteForm.content) {
        message.error('请填写必填项')
        return
      }
      
      if (this.editingNote) {
        // 编辑现有笔记
        const index = this.notes.findIndex(note => note.id === this.editingNote.id)
        if (index !== -1) {
          this.notes[index] = {
            ...this.notes[index],
            ...this.noteForm,
            updateTime: new Date().toISOString()
          }
        }
        message.success('笔记更新成功')
      } else {
        // 创建新笔记
        const newNote = {
          id: Date.now(),
          ...this.noteForm,
          createTime: new Date().toISOString(),
          updateTime: new Date().toISOString()
        }
        this.notes.unshift(newNote)
        message.success('笔记创建成功')
      }
      
      this.cancelEdit()
    },
    deleteNote(note) {
      this.$confirm({
        title: '确认删除',
        content: '确定要删除这条笔记吗？',
        onOk: () => {
          const index = this.notes.findIndex(n => n.id === note.id)
          if (index !== -1) {
            this.notes.splice(index, 1)
            message.success('笔记删除成功')
          }
        }
      })
    },
    searchNotes() {
      // 搜索功能通过 computed 属性实现
    },
    filterNotes() {
      // 筛选功能通过 computed 属性实现
    },
    formatDate(dateString) {
      const date = new Date(dateString)
      const now = new Date()
      const diff = now - date
      
      if (diff < 60000) return '刚刚'
      if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
      if (diff < 2592000000) return `${Math.floor(diff / 86400000)}天前`
      
      return date.toLocaleDateString('zh-CN')
    }
  }
}
</script>

<style scoped>
.notes-container {
  padding: 0;
  min-height: calc(100vh - 120px);
  background: #fafbfc;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

/* 网格视图 */
.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  padding: 0 24px;
}

.note-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  height: 200px;
}

.note-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.note-header {
  margin-bottom: 12px;
}

.note-title {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 4px;
  line-height: 1.4;
}

.note-subject {
  font-size: 12px;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  padding: 2px 8px;
  border-radius: 12px;
  display: inline-block;
}

.note-content {
  flex: 1;
  font-size: 14px;
  color: #595959;
  line-height: 1.6;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.note-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.note-date {
  font-size: 12px;
  color: #8c8c8c;
}

.note-actions {
  display: flex;
  gap: 4px;
}

/* 列表视图 */
.notes-list {
  padding: 0 24px;
}

.note-title-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.note-content-cell {
  color: #595959;
  line-height: 1.6;
}

.note-time-cell {
  color: #8c8c8c;
  font-size: 13px;
}

.note-actions-cell {
  display: flex;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .toolbar-left {
    flex-direction: column;
    gap: 8px;
  }
  
  .notes-grid {
    grid-template-columns: 1fr;
    padding: 0 16px;
  }
  
  .notes-list {
    padding: 0 16px;
  }
}
</style>