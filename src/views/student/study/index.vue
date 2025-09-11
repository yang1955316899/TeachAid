<template>
  <div class="study-container">
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
            <div class="selection-text">已选择: "{{ selectedText.substring(0, 30) }}..."</div>
            <a-button
              type="primary"
              size="small"
              @click="askAI"
              class="ask-button"
            >
              <RobotOutlined /> 询问AI
            </a-button>
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
            <div class="input-wrapper">
              <a-textarea
                v-model:value="inputMessage"
                placeholder="输入你的问题... (Ctrl+Enter 发送)"
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
  BookOutlined
} from '@ant-design/icons-vue'

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
    BookOutlined
  },
  data() {
    return {
      currentQuestion: 1,
      totalQuestions: 5,
      selectedText: '',
      inputMessage: '',
      sending: false,
      regenerating: false,
      isLiked: false,
      isReading: false,
      chatMessages: [
        {
          id: 1,
          role: 'assistant',
          content: '你好！我是你的AI学习助手，有什么问题可以随时问我。我会引导你一步步思考，而不是直接给出答案 😊',
          time: '09:00'
        }
      ],
      questions: [
        {
          id: 1,
          title: '二次函数的图像与性质',
          subject: '数学',
          content: '<p>已知二次函数 f(x) = ax² + bx + c，其中 a > 0...</p>',
          rewrittenAnswer: '<p>让我们一步步来分析这个二次函数问题...</p>'
        }
      ]
    }
  },
  computed: {
    currentQuestionData() {
      return this.questions[this.currentQuestion - 1] || {}
    },
    progressGradient() {
      return {
        '0%': '#3b82f6',
        '50%': '#06b6d4',
        '100%': '#10b981'
      }
    }
  },
  methods: {
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
    askAI() {
      if (this.selectedText) {
        this.inputMessage = `我对这部分内容有疑问：「${this.selectedText}」`
        this.sendMessage()
        this.selectedText = ''
      }
    },
    async sendMessage() {
      if (!this.inputMessage.trim() || this.sending) return

      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: this.inputMessage,
        time: new Date().toLocaleTimeString('zh-CN', { hour12: false }).slice(0, 5)
      }

      this.chatMessages.push(userMessage)
      this.inputMessage = ''
      this.sending = true

      // 模拟AI回复
      setTimeout(() => {
        const aiMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: '这是一个很好的问题！让我来帮你分析一下...',
          time: new Date().toLocaleTimeString('zh-CN', { hour12: false }).slice(0, 5)
        }
        this.chatMessages.push(aiMessage)
        this.sending = false
        this.scrollToBottom()
      }, 1000)

      this.scrollToBottom()
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
      this.chatMessages = [
        {
          id: 1,
          role: 'assistant',
          content: '对话已清空，有什么新问题可以随时问我！',
          time: new Date().toLocaleTimeString('zh-CN', { hour12: false }).slice(0, 5)
        }
      ]
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
  padding: 0;
  min-height: calc(100vh - 120px);
  background: #fafbfc;
}

/* 顶部控制区 */
.study-header {
  background: white;
  padding: 24px;
  border-radius: 16px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  height: calc(100vh - 240px);
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
  top: 20px;
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
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border: 1px solid #e6f7ff;
  display: flex;
  align-items: center;
  gap: 12px;
  animation: slideUp 0.3s ease;
}

.selection-text {
  font-size: 12px;
  color: #595959;
}

.ask-button {
  border-radius: 8px;
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

/* 响应式 */
@media (max-width: 1200px) {
  .study-content {
    flex-direction: column;
    height: auto;
  }
  
  .content-right {
    width: 100%;
    height: 500px;
  }
}
</style>