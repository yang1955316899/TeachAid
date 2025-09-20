<template>
  <div class="study-container">
    <!-- 学习选择区域 -->
    <div class="study-selector">
      <div class="selector-header">
        <h2><BookOutlined /> 智能学习</h2>
        <div class="selector-actions">
          <a-button @click="refreshData" :loading="loadingData">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="selector-content">
        <div class="selector-row">
          <div class="selector-item">
            <label>学习模式</label>
            <a-radio-group v-model:value="studyMode" @change="onStudyModeChange">
              <a-radio-button value="free">自由学习</a-radio-button>
              <a-radio-button value="homework">作业练习</a-radio-button>
            </a-radio-group>
          </div>
        </div>

        <div class="selector-row">
          <div class="selector-item">
            <label>学科</label>
            <a-select
              v-model:value="selectedSubject"
              placeholder="选择学科"
              style="width: 200px"
              :loading="taxonomyStore.loading"
              @change="onSubjectChange"
              allowClear
            >
              <a-select-option
                v-for="subject in taxonomyStore.subjectOptions"
                :key="subject.value"
                :value="subject.value"
              >
                {{ subject.label }}
              </a-select-option>
            </a-select>
          </div>

          <div class="selector-item" v-if="studyMode === 'homework'">
            <label>作业</label>
            <a-select
              v-model:value="selectedHomework"
              placeholder="选择作业"
              style="width: 300px"
              :loading="homeworkStore.loading"
              @change="onHomeworkChange"
              allowClear
            >
              <a-select-option
                v-for="homework in homeworkStore.homeworkOptions"
                :key="homework.value"
                :value="homework.value"
              >
                <div class="homework-option">
                  <span class="homework-title">{{ homework.label }}</span>
                  <a-tag :color="getStatusColor(homework.status)" size="small">
                    {{ getStatusText(homework.status) }}
                  </a-tag>
                </div>
              </a-select-option>
            </a-select>
          </div>

          <div class="selector-item">
            <label>难度</label>
            <a-select
              v-model:value="selectedDifficulty"
              placeholder="选择难度"
              style="width: 150px"
              @change="onFilterChange"
              allowClear
            >
              <a-select-option value="easy">简单</a-select-option>
              <a-select-option value="medium">中等</a-select-option>
              <a-select-option value="hard">困难</a-select-option>
            </a-select>
          </div>

          <div class="selector-item">
            <a-button type="primary" @click="startStudy" :disabled="!canStartStudy" :loading="loadingQuestions">
              <PlayCircleOutlined /> 开始学习
            </a-button>
          </div>
        </div>

        <div class="study-stats" v-if="studyStats.total > 0">
          <a-statistic-countdown
            :value="studyStats.total"
            format="共 [0] 道题目"
            :value-style="{fontSize: '14px'}"
          />
          <span class="divider">|</span>
          <span>{{ studyStats.subject }}</span>
          <span class="divider" v-if="studyStats.homework">|</span>
          <span v-if="studyStats.homework">{{ studyStats.homework }}</span>
        </div>
      </div>
    </div>

    <!-- 学习进行中的界面 -->
    <div class="study-area" v-show="isStudying">
      <!-- 顶部进度条和控制 -->
      <div class="study-header">
      <div class="progress-section">
        <div class="progress-text">
          <span class="current-question">第 {{ currentQuestion }} 题</span>
          <span class="total-questions">共 {{ totalQuestions }} 题</span>
        </div>
        <a-progress 
          :percent="(currentQuestion / totalQuestions) * 100" 
          :show-info="false"
          :stroke-color="progressGradient"
          :stroke-width="8"
          class="progress-bar"
        />
      </div>
      <div class="control-buttons">
        <a-button 
          @click="prevQuestion" 
          :disabled="currentQuestion === 1"
          class="nav-button"
        >
          <LeftOutlined /> 上一题
        </a-button>
        <a-button 
          @click="nextQuestion" 
          :disabled="currentQuestion === totalQuestions"
          class="nav-button"
          type="primary"
        >
          下一题 <RightOutlined />
        </a-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="study-content">
      <div class="content-left">
        <!-- 题目卡片 -->
        <div class="question-card">
          <div class="card-header">
            <div class="question-number"># {{ currentQuestion }}</div>
            <div class="question-category">
              <span class="subject-badge">{{ currentQuestionData.subject || '数学' }}</span>
              <span class="type-badge">解答题</span>
            </div>
          </div>
          
          <div class="question-content">
            <h3>{{ currentQuestionData.title }}</h3>
            <div class="question-body" v-html="currentQuestionData.content || '已知二次函数 f(x) = ax² + bx + c，其中 a > 0，求函数的最值。'"></div>
          </div>
        </div>

        <!-- 答案卡片 -->
        <div class="answer-card">
          <div class="card-header">
            <h3>
              <BulbOutlined /> AI改写答案
            </h3>
            <div class="answer-actions">
              <a-tooltip title="重新生成答案">
                <a-button 
                  type="text" 
                  size="small" 
                  @click="regenerateAnswer"
                  :loading="regenerating"
                  class="action-button"
                >
                  <ReloadOutlined :class="{ 'rotating': regenerating }" />
                </a-button>
              </a-tooltip>
              <a-tooltip title="复制答案">
                <a-button 
                  type="text" 
                  size="small" 
                  @click="copyAnswer"
                  class="action-button"
                >
                  <CopyOutlined />
                </a-button>
              </a-tooltip>
              <a-tooltip title="选中文字可以直接向AI提问">
                <QuestionCircleOutlined style="color: #999;" />
              </a-tooltip>
            </div>
          </div>
          
          <div class="answer-content" @mouseup="handleTextSelection">
            <div 
              :class="{ 'answer-loading': regenerating }"
              v-html="currentQuestionData.rewrittenAnswer || '让我们一步步来分析这个二次函数问题。首先，你觉得应该从哪个角度来思考这个问题呢？'"
            ></div>
          </div>
          
          <!-- 文本选择提示 -->
          <div v-if="selectedText" class="selection-popup">
            <div class="selection-text">已选择文本: "{{ selectedText.substring(0, 30) }}{{ selectedText.length > 30 ? '...' : '' }}"</div>
            <div class="selection-hint">💡 可以在右侧AI助手中询问相关问题</div>
          </div>
          
          <!-- 浮动工具栏 -->
          <div class="floating-toolbar">
            <a-tooltip title="点赞答案">
              <a-button 
                type="text" 
                @click="likeAnswer" 
                :class="{ 'active': isLiked }"
                class="toolbar-button"
              >
                <HeartOutlined />
              </a-button>
            </a-tooltip>
            <a-tooltip title="语音朗读">
              <a-button 
                type="text" 
                @click="readAloud" 
                :class="{ 'active': isReading }"
                class="toolbar-button"
              >
                <SoundOutlined />
              </a-button>
            </a-tooltip>
            <a-tooltip title="保存笔记">
              <a-button 
                type="text" 
                @click="saveNote"
                class="toolbar-button"
              >
                <BookOutlined />
              </a-button>
            </a-tooltip>
          </div>
        </div>
      </div>

      <!-- AI助手面板 -->
      <div class="content-right">
        <div class="chat-card">
          <div class="chat-header">
            <div class="ai-avatar">
              <RobotOutlined />
            </div>
            <div class="ai-info">
              <div class="ai-name">AI学习助手</div>
              <div class="ai-status">
                <div class="status-dot"></div>
                在线
              </div>
            </div>
            <div class="chat-actions">
              <a-tooltip title="清空对话">
                <a-button type="text" size="small" @click="clearChat">
                  <DeleteOutlined />
                </a-button>
              </a-tooltip>
            </div>
          </div>

          <div class="chat-messages" ref="messagesContainer">
            <div
              v-for="message in chatMessages"
              :key="message.id"
              :class="['message', message.role]"
            >
              <div v-if="message.role === 'assistant'" class="message-avatar">
                <RobotOutlined />
              </div>
              
              <div class="message-bubble">
                <div class="message-content">{{ message.content }}</div>
                <div class="message-time">{{ message.time }}</div>
              </div>
            </div>

            <div v-if="sending" class="message assistant typing">
              <div class="message-avatar">
                <RobotOutlined />
              </div>
              <div class="message-bubble">
                <div class="typing-animation">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>

          <div class="chat-input">
            <!-- 选择文本提示 -->
            <div v-if="selectedText" class="selected-text-hint">
              <div class="hint-content">
                <span class="hint-icon">✨</span>
                <span class="hint-text">你选择了: "{{ selectedText.substring(0, 50) }}{{ selectedText.length > 50 ? '...' : '' }}"</span>
                <a-button 
                  type="text" 
                  size="small" 
                  @click="clearSelection"
                  class="clear-selection"
                >
                  <CloseOutlined />
                </a-button>
              </div>
            </div>
            
            <div class="input-wrapper">
              <a-textarea
                v-model:value="inputMessage"
                :placeholder="selectedText ? '询问关于选中内容的问题...' : '输入你的问题... (Ctrl+Enter 发送)'"
                :auto-size="{ minRows: 1, maxRows: 3 }"
                @keydown.ctrl.enter="sendMessage"
                class="chat-textarea"
              />
              <a-button
                type="primary"
                @click="sendMessage"
                :loading="sending"
                :disabled="!inputMessage.trim()"
                class="send-button"
              >
                <SendOutlined />
              </a-button>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script>
import {
  LeftOutlined,
  RightOutlined,
  BulbOutlined,
  QuestionCircleOutlined,
  RobotOutlined,
  DeleteOutlined,
  SendOutlined,
  ReloadOutlined,
  CopyOutlined,
  HeartOutlined,
  SoundOutlined,
  BookOutlined,
  CloseOutlined,
  PlayCircleOutlined
} from '@ant-design/icons-vue'
import { useQuestionStore } from '@/stores/question'
import { useTaxonomyStore } from '@/stores/taxonomy'
import { useHomeworkStore } from '@/stores/homework'
import { message } from 'ant-design-vue'
import { useChatStore } from '@/stores/chat'
import { storeToRefs } from 'pinia'

export default {
  name: 'StudentStudy',
  components: {
    LeftOutlined,
    RightOutlined,
    BulbOutlined,
    QuestionCircleOutlined,
    RobotOutlined,
    DeleteOutlined,
    SendOutlined,
    ReloadOutlined,
    CopyOutlined,
    HeartOutlined,
    SoundOutlined,
    BookOutlined,
    CloseOutlined,
    PlayCircleOutlined
  },
  data() {
    return {
      // 学习选择相关
      studyMode: 'free', // 'free' | 'homework'
      selectedSubject: null,
      selectedHomework: null,
      selectedDifficulty: null,
      isStudying: false,
      loadingData: false,
      studyStats: {
        total: 0,
        subject: '',
        homework: ''
      },

      // 学习进行相关
      currentQuestion: 1,
      selectedText: '',
      inputMessage: '',
      sending: false,
      regenerating: false,
      isLiked: false,
      isReading: false,
      loadingQuestions: false
    }
  },
  computed: {
    questionStore() {
      return useQuestionStore()
    },
    taxonomyStore() {
      return useTaxonomyStore()
    },
    homeworkStore() {
      return useHomeworkStore()
    },
    chatStore() {
      return useChatStore()
    },
    questions() {
      return this.questionStore.questions
    },
    totalQuestions() {
      return this.questions.length || 0
    },
    chatMessages() {
      return this.chatStore.messages
    },
    currentQuestionData() {
      return this.questions[this.currentQuestion - 1] || {}
    },
    progressGradient() {
      return {
        '0%': '#3b82f6',
        '50%': '#06b6d4',
        '100%': '#10b981'
      }
    },
    canStartStudy() {
      if (this.studyMode === 'homework') {
        return this.selectedHomework
      }
      return this.selectedSubject || this.questions.length > 0
    }
  },
  async mounted() {
    await this.initializeData()
  },
  methods: {
    /**
     * 初始化数据
     */
    async initializeData() {
      this.loadingData = true
      try {
        // 并行加载基础数据
        await Promise.all([
          this.taxonomyStore.fetchSubjects(),
          this.loadDefaultQuestions()
        ])
      } catch (error) {
        console.error('初始化数据失败:', error)
        message.error('初始化数据失败')
      } finally {
        this.loadingData = false
      }
    },

    /**
     * 加载默认题目（不筛选）
     */
    async loadDefaultQuestions() {
      try {
        const response = await this.questionStore.fetchQuestions({
          page: 1,
          size: 20,
          is_public: true
        })
        this.updateStudyStats()
      } catch (error) {
        console.error('加载默认题目失败:', error)
      }
    },

    /**
     * 根据选择条件加载题目
     */
    async loadQuestions() {
      this.loadingQuestions = true
      try {
        const params = {
          page: 1,
          size: 50,
          is_public: true
        }

        // 添加筛选条件
        if (this.selectedSubject) {
          params.subject_id = this.selectedSubject
        }
        if (this.selectedDifficulty) {
          params.difficulty = this.selectedDifficulty
        }

        // 如果是作业模式，需要特殊处理
        if (this.studyMode === 'homework' && this.selectedHomework) {
          await this.loadHomeworkQuestions()
        } else {
          await this.questionStore.fetchQuestions(params)
        }

        this.updateStudyStats()
      } catch (error) {
        console.error('加载题目失败:', error)
        message.error('加载题目失败')
      } finally {
        this.loadingQuestions = false
      }
    },

    /**
     * 加载作业题目
     */
    async loadHomeworkQuestions() {
      const homework = await this.homeworkStore.fetchStudentHomework(this.selectedHomework)
      if (homework && homework.question_ids) {
        // 根据作业中的题目ID获取题目
        const response = await this.questionStore.fetchQuestions({
          ids: homework.question_ids.join(','),
          is_public: true
        })
      }
    },

    /**
     * 更新学习统计信息
     */
    updateStudyStats() {
      this.studyStats.total = this.totalQuestions

      // 获取学科名称
      if (this.selectedSubject) {
        const subject = this.taxonomyStore.subjects.find(s => s.id === this.selectedSubject)
        this.studyStats.subject = subject ? subject.name : ''
      } else {
        this.studyStats.subject = '全部学科'
      }

      // 获取作业名称
      if (this.selectedHomework) {
        const homework = this.homeworkStore.studentHomeworks.find(h => h.id === this.selectedHomework)
        this.studyStats.homework = homework ? homework.title : ''
      } else {
        this.studyStats.homework = ''
      }
    },

    /**
     * 学习模式变更
     */
    async onStudyModeChange() {
      this.selectedHomework = null
      this.isStudying = false

      if (this.studyMode === 'homework') {
        // 加载学生作业列表
        await this.homeworkStore.fetchStudentHomeworks({
          status: ['assigned', 'in_progress'],
          page: 1,
          size: 50
        })
      }

      await this.loadQuestions()
    },

    /**
     * 学科选择变更
     */
    async onSubjectChange() {
      this.isStudying = false
      await this.loadQuestions()
    },

    /**
     * 作业选择变更
     */
    async onHomeworkChange() {
      this.isStudying = false
      if (this.selectedHomework) {
        await this.loadQuestions()
      }
    },

    /**
     * 筛选条件变更
     */
    async onFilterChange() {
      this.isStudying = false
      await this.loadQuestions()
    },

    /**
     * 开始学习
     */
    async startStudy() {
      if (!this.canStartStudy) {
        message.warning('请先选择学习内容')
        return
      }

      if (this.totalQuestions === 0) {
        message.warning('没有找到相关题目，请调整筛选条件')
        return
      }

      this.isStudying = true
      this.currentQuestion = 1

      // 如果是作业模式，开始作业
      if (this.studyMode === 'homework' && this.selectedHomework) {
        try {
          await this.homeworkStore.startHomework(this.selectedHomework)
        } catch (error) {
          console.error('开始作业失败:', error)
        }
      }

      message.success('开始学习！')
    },

    /**
     * 刷新数据
     */
    async refreshData() {
      await this.initializeData()
      message.success('刷新成功')
    },

    /**
     * 获取作业状态颜色
     */
    getStatusColor(status) {
      const colors = {
        'assigned': 'blue',
        'pending': 'blue',
        'in_progress': 'orange',
        'completed': 'green',
        'overdue': 'red'
      }
      return colors[status] || 'default'
    },

    /**
     * 获取作业状态文本
     */
    getStatusText(status) {
      const texts = {
        'assigned': '已布置',
        'pending': '待开始',
        'in_progress': '进行中',
        'completed': '已完成',
        'overdue': '已过期'
      }
      return texts[status] || status
    },

    prevQuestion() {
      if (this.currentQuestion > 1) {
        this.currentQuestion--
      }
    },
    nextQuestion() {
      if (this.currentQuestion < this.totalQuestions) {
        this.currentQuestion++
      }
    },
    handleTextSelection() {
      const selection = window.getSelection()
      if (selection.rangeCount > 0 && selection.toString().trim()) {
        this.selectedText = selection.toString().trim()
      } else {
        this.selectedText = ''
      }
    },
    clearSelection() {
      this.selectedText = ''
    },
    async sendMessage() {
      if (!this.inputMessage.trim() || this.sending) return

      this.sending = true
      try {
        // 确保有活跃的对话会话
        if (!this.chatStore.currentSession && this.currentQuestionData) {
          await this.chatStore.startChatSession(this.currentQuestionData.id)
        }

        // 发送消息
        await this.chatStore.sendMessage(this.inputMessage, this.selectedText)
        
        this.inputMessage = ''
        this.selectedText = '' // 发送后清除选择
        this.scrollToBottom()
      } catch (error) {
        console.error('发送消息失败:', error)
        this.$message.error('发送消息失败')
      } finally {
        this.sending = false
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    },
    clearChat() {
      this.chatStore.clearCurrentSession()
    },
    async regenerateAnswer() {
      this.regenerating = true
      try {
        // 模拟重新生成答案
        await new Promise(resolve => setTimeout(resolve, 2000))
        // 这里可以调用API重新生成答案
        this.$message.success('答案已重新生成')
      } catch (error) {
        this.$message.error('生成失败，请重试')
      } finally {
        this.regenerating = false
      }
    },
    copyAnswer() {
      const answerText = this.currentQuestionData.rewrittenAnswer || '暂无答案'
      // 移除HTML标签
      const textContent = answerText.replace(/<[^>]*>/g, '')
      
      if (navigator.clipboard) {
        navigator.clipboard.writeText(textContent).then(() => {
          this.$message.success('答案已复制到剪贴板')
        })
      } else {
        // 兼容旧版浏览器
        const textArea = document.createElement('textarea')
        textArea.value = textContent
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
        this.$message.success('答案已复制到剪贴板')
      }
    },
    likeAnswer() {
      this.isLiked = !this.isLiked
      if (this.isLiked) {
        this.$message.success('感谢您的反馈！')
      }
    },
    readAloud() {
      if (this.isReading) {
        // 停止朗读
        speechSynthesis.cancel()
        this.isReading = false
        return
      }
      
      // 开始朗读
      const answerText = this.currentQuestionData.rewrittenAnswer || '暂无答案'
      const textContent = answerText.replace(/<[^>]*>/g, '')
      
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(textContent)
        utterance.lang = 'zh-CN'
        utterance.rate = 0.8
        utterance.pitch = 1
        
        utterance.onstart = () => {
          this.isReading = true
        }
        
        utterance.onend = () => {
          this.isReading = false
        }
        
        utterance.onerror = () => {
          this.isReading = false
          this.$message.error('朗读功能暂不可用')
        }
        
        speechSynthesis.speak(utterance)
      } else {
        this.$message.error('您的浏览器不支持语音朗读功能')
      }
    },
    saveNote() {
      // 这里可以实现保存笔记的功能
      this.$message.success('笔记已保存')
    }
  }
}
</script>

<style scoped>
/* 学习容器 */
.study-container {
  padding: 24px;
  min-height: calc(100vh - 120px);
  background: #fafbfc;
}

/* 学习选择区域 */
.study-selector {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  margin-bottom: 24px;
  overflow: hidden;
}

.selector-header {
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selector-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
}

.selector-actions .ant-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
}

.selector-actions .ant-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
}

.selector-content {
  padding: 24px;
}

.selector-row {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
}

.selector-row:last-child {
  margin-bottom: 0;
}

.selector-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selector-item label {
  font-weight: 500;
  color: #262626;
  font-size: 14px;
}

.homework-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.homework-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.study-stats {
  padding: 16px 20px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #495057;
  margin-top: 16px;
}

.divider {
  color: #dee2e6;
  font-weight: 300;
}

/* 学习区域 */
.study-area {
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 顶部控制区 */
.study-header {
  background: white;
  padding: 20px 24px;
  border-radius: 16px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 24px;
  z-index: 10;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
}

.progress-section {
  flex: 1;
  margin-right: 24px;
}

.progress-text {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.current-question {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.total-questions {
  font-size: 14px;
  color: #8c8c8c;
}

.progress-bar {
  margin: 0;
}

.control-buttons {
  display: flex;
  gap: 12px;
}

.nav-button {
  border-radius: 8px;
  font-weight: 500;
}

/* 主要内容区 */
.study-content {
  display: flex;
  gap: 24px;
  min-height: calc(100vh - 300px);
}

.content-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.content-right {
  width: 400px;
}

/* 题目卡片 */
.question-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  overflow: hidden;
}

.question-card .card-header {
  padding: 20px 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-number {
  font-size: 24px;
  font-weight: 700;
}

.question-category {
  display: flex;
  gap: 8px;
}

.subject-badge, .type-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.subject-badge {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}

.type-badge {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
}

.question-content {
  padding: 24px;
}

.question-content h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.question-body {
  font-size: 14px;
  line-height: 1.6;
  color: #595959;
}

/* 答案卡片 */
.answer-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
}

.answer-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.answer-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.answer-card .card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  display: flex;
  align-items: center;
  gap: 8px;
}

.answer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-button {
  transition: all 0.3s ease;
  border-radius: 6px;
}

.action-button:hover {
  background: #f0f9ff;
  color: #3b82f6;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.answer-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  cursor: text;
  user-select: text;
  font-size: 14px;
  line-height: 1.6;
  color: #595959;
  position: relative;
}

.answer-loading {
  opacity: 0.6;
  position: relative;
}

.answer-loading::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* 浮动工具栏 */
.floating-toolbar {
  position: absolute;
  top: 100px;
  right: 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  flex-direction: column;
  gap: 4px;
  opacity: 0;
  transform: translateX(10px);
  transition: all 0.3s ease;
}

.answer-card:hover .floating-toolbar {
  opacity: 1;
  transform: translateX(0);
}

.toolbar-button {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.3s ease;
  color: #64748b;
}

.toolbar-button:hover {
  background: #f1f5f9;
  color: #3b82f6;
  transform: scale(1.1);
}

.toolbar-button.active {
  background: #3b82f6;
  color: white;
}

.selection-popup {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.2);
  animation: slideUp 0.3s ease;
  max-width: 300px;
}

.selection-text {
  font-size: 12px;
  color: #3b82f6;
  font-weight: 500;
  margin-bottom: 4px;
}

.selection-hint {
  font-size: 11px;
  color: #64748b;
  line-height: 1.4;
}

@keyframes slideUp {
  from { transform: translateY(10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* 聊天卡片 */
.chat-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.ai-info {
  flex: 1;
}

.ai-name {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.ai-status {
  font-size: 12px;
  color: #52c41a;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #52c41a;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  animation: messageIn 0.3s ease;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  flex-shrink: 0;
}

.message-bubble {
  max-width: 70%;
  position: relative;
}

.message.user .message-bubble {
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  color: white;
  border-radius: 16px 16px 4px 16px;
}

.message.assistant .message-bubble {
  background: #f8f9fa;
  color: #262626;
  border-radius: 16px 16px 16px 4px;
}

.message-content {
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.5;
}

.message-time {
  font-size: 11px;
  opacity: 0.7;
  padding: 4px 16px 8px 16px;
}

.typing-animation {
  padding: 12px 16px;
  display: flex;
  gap: 4px;
}

.typing-animation span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #bbb;
  animation: typing 1.4s infinite;
}

.typing-animation span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-animation span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-10px); }
}

@keyframes messageIn {
  from { transform: translateY(10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* 输入区 */
.chat-input {
  padding: 20px;
  border-top: 1px solid #f0f0f0;
}

/* 选择文本提示 */
.selected-text-hint {
  margin-bottom: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 12px;
  animation: slideDown 0.3s ease;
}

.hint-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hint-icon {
  font-size: 14px;
}

.hint-text {
  flex: 1;
  font-size: 13px;
  color: #3b82f6;
  font-weight: 500;
  line-height: 1.4;
}

.clear-selection {
  color: #64748b;
  padding: 4px;
  min-width: auto;
  height: auto;
}

.clear-selection:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

@keyframes slideDown {
  from { transform: translateY(-10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-textarea {
  flex: 1;
  border-radius: 12px;
  border: 2px solid #e6f7ff;
  transition: all 0.3s ease;
}

.chat-textarea:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.send-button {
  border-radius: 12px;
  height: 40px;
  width: 40px;
  padding: 0;
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.send-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
}

.send-button:disabled {
  transform: none;
  box-shadow: none;
  opacity: 0.5;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .study-content {
    flex-direction: column;
    min-height: auto;
  }

  .content-right {
    width: 100%;
    height: 500px;
  }

  .selector-row {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .selector-item {
    width: 100%;
  }

  .selector-item .ant-select {
    width: 100% !important;
  }
}

@media (max-width: 768px) {
  .study-container {
    padding: 16px;
  }

  .study-selector {
    margin-bottom: 16px;
  }

  .selector-header {
    padding: 16px;
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }

  .selector-content {
    padding: 16px;
  }

  .study-header {
    padding: 16px;
    margin-bottom: 16px;
    flex-direction: column;
    gap: 16px;
    position: static;
  }

  .progress-section {
    margin-right: 0;
    margin-bottom: 12px;
  }

  .control-buttons {
    gap: 8px;
    justify-content: center;
    width: 100%;
  }

  .nav-button {
    flex: 1;
    max-width: 120px;
  }

  .question-card,
  .answer-card {
    margin-bottom: 16px;
  }

  .question-card .card-header {
    padding: 16px;
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }

  .question-content {
    padding: 16px;
  }

  .chat-card {
    height: 400px;
  }

  .floating-toolbar {
    position: fixed;
    bottom: 80px;
    right: 16px;
    flex-direction: row;
    opacity: 1;
    transform: none;
    gap: 8px;
  }

  .study-stats {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }

  .study-stats .divider {
    display: none;
  }
}

@media (max-width: 480px) {
  .study-container {
    padding: 12px;
  }

  .selector-header h2 {
    font-size: 18px;
  }

  .question-number {
    font-size: 20px !important;
  }

  .question-content h3 {
    font-size: 16px;
  }

  .answer-card .card-header h3 {
    font-size: 14px;
  }

  .chat-messages {
    padding: 12px;
  }

  .message-bubble {
    max-width: 85%;
  }

  .chat-input {
    padding: 12px;
  }

  .toolbar-button {
    width: 28px;
    height: 28px;
  }
}
</style>
