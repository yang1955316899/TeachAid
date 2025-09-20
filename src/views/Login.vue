<template>
  <div class="login-container">
    <!-- 动态粒子背景 -->
    <div class="particle-background">
      <canvas ref="particleCanvas" class="particle-canvas"></canvas>
    </div>

    <!-- 动态网格 -->
    <div class="grid-background">
      <div class="grid-lines"></div>
    </div>

    <!-- 浮动几何体 -->
    <div class="floating-geometry">
      <div class="geometry-item geo-1"></div>
      <div class="geometry-item geo-2"></div>
      <div class="geometry-item geo-3"></div>
      <div class="geometry-item geo-4"></div>
      <div class="geometry-item geo-5"></div>
      <div class="geometry-item geo-6"></div>
    </div>

    <!-- 左侧内容区 -->
    <div class="content-left">
      <div class="brand-section">
        <div class="logo-container">
          <div class="logo-icon">
            <div class="logo-inner">
              <div class="logo-cube">
                <div class="cube-face front"></div>
                <div class="cube-face back"></div>
                <div class="cube-face left"></div>
                <div class="cube-face right"></div>
                <div class="cube-face top"></div>
                <div class="cube-face bottom"></div>
              </div>
            </div>
          </div>
          <h1 class="brand-title">
            <span class="main-title">TeachAI</span>
            <div class="typewriter-container">
              <span class="typewriter-text">{{ currentText }}</span>
              <span class="cursor" :class="{ 'blinking': isBlinking }">|</span>
            </div>
          </h1>
        </div>
        <p class="brand-subtitle">
          <span class="gradient-text">AI驱动的未来教育平台</span>
        </p>
        <div class="stats-list">
          <div class="stat-item">
            <span class="stat-number">10+</span>
            <span class="stat-label">题目库</span>
          </div>
          <div class="stat-item">
            <span class="stat-number">98%+</span>
            <span class="stat-label">准确率</span>
          </div>
          <div class="stat-item">
            <span class="stat-number">5+</span>
            <span class="stat-label">活跃用户</span>
          </div>
        </div>
        
        <div class="tech-tags">
          <span class="tech-tag">LangGraph</span>
          <span class="tech-tag">QwenVL</span>
          <span class="tech-tag">Qwen</span>
        </div>
      </div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="content-right">
      <div class="login-form">
        <div class="form-header">
          <h2>欢迎回来</h2>
          <p>请登录您的账户</p>
        </div>
        
        <a-form
          :model="form"
          @finish="handleLogin"
          layout="vertical"
          class="login-form-content"
        >
          <a-form-item
            name="username"
            :rules="[{ required: true, message: '请输入用户名!' }]"
          >
            <a-input
              v-model:value="form.username"
              placeholder="请输入用户名"
              size="large"
              class="form-input"
              autocomplete="username"
            >
              <template #prefix>
                <UserOutlined style="color: rgba(0,0,0,.25)" />
              </template>
            </a-input>
          </a-form-item>

          <a-form-item
            name="password"
            :rules="[{ required: true, message: '请输入密码!' }]"
          >
            <a-input-password
              v-model:value="form.password"
              placeholder="请输入密码"
              size="large"
              class="form-input"
              autocomplete="current-password"
            >
              <template #prefix>
                <LockOutlined style="color: rgba(0,0,0,.25)" />
              </template>
            </a-input-password>
          </a-form-item>

          <a-form-item>
            <a-button 
              type="primary" 
              html-type="submit" 
              block 
              size="large"
              :loading="loading"
              class="login-button"
            >
              <span v-if="!loading">立即登录</span>
            </a-button>
          </a-form-item>
        </a-form>

      </div>
    </div>
  </div>
</template>

<script>
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'Login',
  components: {
    UserOutlined,
    LockOutlined
  },
  data() {
    return {
      form: {
        username: '',
        password: ''
      },
      loading: false,
      currentText: '',
      isBlinking: true,
      typewriterTexts: ['AI驱动的智能答案改写', '多模态题目识别与处理', '个性化学习对话助手'],
      currentTextIndex: 0,
      isTyping: true
    }
  },
  mounted() {
    this.initParticles()
    this.startTypewriter()
  },
  methods: {
    async handleLogin() {
      this.loading = true
      try {
        const authStore = useAuthStore()
        const result = await authStore.login(this.form)
        
        if (result.success) {
          // 根据用户角色跳转
          if (authStore.isTeacher) {
            this.$router.push('/teacher/dashboard')
          } else {
            this.$router.push('/student/dashboard')
          }
        } else {
          // 显示错误信息
          this.$message.error(result.message || '登录失败')
        }
      } catch (error) {
        console.error('登录失败:', error)
        const errorMessage = error.response?.data?.detail || error.message || '登录失败，请检查用户名和密码'
        this.$message.error(errorMessage)
      } finally {
        this.loading = false
      }
    },
    initParticles() {
      const canvas = this.$refs.particleCanvas
      if (!canvas) return
      
      const ctx = canvas.getContext('2d')
      const particles = []
      
      // 设置画布大小
      const resizeCanvas = () => {
        canvas.width = canvas.offsetWidth
        canvas.height = canvas.offsetHeight
      }
      
      resizeCanvas()
      window.addEventListener('resize', resizeCanvas)
      
      // 粒子类
      class Particle {
        constructor() {
          this.x = Math.random() * canvas.width
          this.y = Math.random() * canvas.height
          this.vx = (Math.random() - 0.5) * 0.5
          this.vy = (Math.random() - 0.5) * 0.5
          this.radius = Math.random() * 2 + 1
          this.opacity = Math.random() * 0.5 + 0.2
        }
        
        update() {
          this.x += this.vx
          this.y += this.vy
          
          // 边界反弹
          if (this.x < 0 || this.x > canvas.width) this.vx *= -1
          if (this.y < 0 || this.y > canvas.height) this.vy *= -1
          
          // 保持在画布内
          this.x = Math.max(0, Math.min(canvas.width, this.x))
          this.y = Math.max(0, Math.min(canvas.height, this.y))
        }
        
        draw() {
          ctx.beginPath()
          ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(59, 130, 246, ${this.opacity})`
          ctx.fill()
        }
      }
      
      // 创建粒子
      for (let i = 0; i < 80; i++) {
        particles.push(new Particle())
      }
      
      // 动画循环
      const animate = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        
        particles.forEach(particle => {
          particle.update()
          particle.draw()
        })
        
        // 绘制连接线
        particles.forEach((particle, i) => {
          particles.slice(i + 1).forEach(otherParticle => {
            const dx = particle.x - otherParticle.x
            const dy = particle.y - otherParticle.y
            const distance = Math.sqrt(dx * dx + dy * dy)
            
            if (distance < 120) {
              ctx.beginPath()
              ctx.moveTo(particle.x, particle.y)
              ctx.lineTo(otherParticle.x, otherParticle.y)
              ctx.strokeStyle = `rgba(59, 130, 246, ${0.1 * (1 - distance / 120)})`
              ctx.lineWidth = 1
              ctx.stroke()
            }
          })
        })
        
        requestAnimationFrame(animate)
      }
      
      animate()
    },
    startTypewriter() {
      this.typeText()
    },
    async typeText() {
      const currentFullText = this.typewriterTexts[this.currentTextIndex]
      
      if (this.isTyping) {
        // 打字阶段
        for (let i = 0; i <= currentFullText.length; i++) {
          this.currentText = currentFullText.substring(0, i)
          await this.delay(100) // 统一打字速度
        }
        
        // 停顿时间
        await this.delay(2500)
        this.isTyping = false
      } else {
        // 删除阶段
        for (let i = currentFullText.length; i >= 0; i--) {
          this.currentText = currentFullText.substring(0, i)
          await this.delay(50) // 删除速度
        }
        
        // 停顿一下
        await this.delay(300)
        
        // 切换到下一个文本
        this.currentTextIndex = (this.currentTextIndex + 1) % this.typewriterTexts.length
        this.isTyping = true
      }
      
      // 递归调用继续动画
      this.typeText()
    },
    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms))
    }
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
}

/* 粒子背景 */
.particle-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 1;
}

.particle-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

/* 动态网格 */
.grid-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.grid-lines {
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(59, 130, 246, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59, 130, 246, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: gridMove 20s linear infinite;
}

@keyframes gridMove {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

/* 浮动几何体 */
.floating-geometry {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
}

.geometry-item {
  position: absolute;
  background: linear-gradient(45deg, rgba(59, 130, 246, 0.15), rgba(6, 182, 212, 0.15));
  animation: geometryFloat 8s ease-in-out infinite;
}

.geo-1 {
  width: 60px;
  height: 60px;
  top: 15%;
  left: 10%;
  border-radius: 50%;
  animation-delay: 0s;
}

.geo-2 {
  width: 40px;
  height: 40px;
  top: 25%;
  right: 15%;
  border-radius: 8px;
  animation-delay: 1.5s;
}

.geo-3 {
  width: 80px;
  height: 80px;
  bottom: 30%;
  left: 8%;
  clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
  animation-delay: 3s;
}

.geo-4 {
  width: 50px;
  height: 50px;
  bottom: 20%;
  right: 10%;
  border-radius: 50%;
  animation-delay: 4.5s;
}

.geo-5 {
  width: 35px;
  height: 35px;
  top: 60%;
  left: 15%;
  border-radius: 8px;
  transform: rotate(45deg);
  animation-delay: 2s;
}

.geo-6 {
  width: 70px;
  height: 70px;
  top: 40%;
  right: 8%;
  clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%);
  animation-delay: 5s;
}

@keyframes geometryFloat {
  0%, 100% { 
    transform: translateY(0px) rotate(0deg) scale(1);
    opacity: 0.6;
  }
  25% { 
    transform: translateY(-30px) rotate(90deg) scale(1.1);
    opacity: 0.8;
  }
  50% { 
    transform: translateY(-15px) rotate(180deg) scale(0.9);
    opacity: 1;
  }
  75% { 
    transform: translateY(-25px) rotate(270deg) scale(1.05);
    opacity: 0.7;
  }
}

/* 左侧内容区 */
.content-left {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  z-index: 2;
  position: relative;
}

.brand-section {
  max-width: 500px;
  color: white;
}

.logo-container {
  display: flex;
  align-items: flex-start;
  margin-bottom: 32px;
  gap: 20px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  perspective: 1000px;
  flex-shrink: 0;
  margin-top: 8px;
}

.logo-inner {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  animation: logoRotate 10s linear infinite;
}

.logo-cube {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
}

.cube-face {
  position: absolute;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  border: 2px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.cube-face:before {
  content: 'T';
}

.cube-face.front {
  transform: rotateY(0deg) translateZ(24px);
}

.cube-face.back {
  transform: rotateY(180deg) translateZ(24px);
}

.cube-face.right {
  transform: rotateY(90deg) translateZ(24px);
}

.cube-face.left {
  transform: rotateY(-90deg) translateZ(24px);
}

.cube-face.top {
  transform: rotateX(90deg) translateZ(24px);
}

.cube-face.bottom {
  transform: rotateX(-90deg) translateZ(24px);
}

@keyframes logoRotate {
  0% { transform: rotateX(0deg) rotateY(0deg); }
  25% { transform: rotateX(90deg) rotateY(0deg); }
  50% { transform: rotateX(90deg) rotateY(90deg); }
  75% { transform: rotateX(0deg) rotateY(90deg); }
  100% { transform: rotateX(0deg) rotateY(360deg); }
}

.brand-title {
  margin: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.main-title {
  font-size: 56px;
  font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #06b6d4, #10b981);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradientShift 3s ease-in-out infinite;
  line-height: 1;
}

.typewriter-container {
  display: flex;
  align-items: center;
  height: 50px;
  min-width: 450px;
  max-width: 600px;
  flex-wrap: wrap;
  justify-content: flex-start;
}

.typewriter-text {
  font-size: 24px;
  font-weight: 600;
  color: #06b6d4;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  text-shadow: 0 0 20px rgba(6, 182, 212, 0.5);
  transition: all 0.3s ease;
  line-height: 1.2;
}

.typewriter-text.solgen-highlight {
  font-size: 36px;
  background: linear-gradient(135deg, #06b6d4, #3b82f6, #10b981);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: solgenGlow 2s ease-in-out infinite;
  transform: scale(1.1);
  font-weight: 700;
  text-shadow: 0 0 30px rgba(6, 182, 212, 0.8), 0 0 50px rgba(59, 130, 246, 0.6);
}

@keyframes solgenGlow {
  0%, 100% {
    background-position: 0% 50%;
    filter: brightness(1) drop-shadow(0 0 10px rgba(6, 182, 212, 0.6));
  }
  50% {
    background-position: 100% 50%;
    filter: brightness(1.2) drop-shadow(0 0 20px rgba(59, 130, 246, 0.8));
  }
}

.cursor {
  font-size: 24px;
  color: #06b6d4;
  font-weight: 300;
  margin-left: 2px;
  text-shadow: 0 0 20px rgba(6, 182, 212, 0.8);
}

.cursor.blinking {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@keyframes gradientShift {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.brand-subtitle {
  font-size: 18px;
  margin-bottom: 40px;
  line-height: 1.6;
}

.gradient-text {
  background: linear-gradient(135deg, #06b6d4, #3b82f6, #8b5cf6);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradientShift 4s ease-in-out infinite;
  font-weight: 500;
}

/* 统计数据 */
.stats-list {
  display: flex;
  gap: 32px;
  margin-bottom: 32px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 500;
}

/* 技术标签 */
.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.tech-tag {
  padding: 6px 12px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  color: #3b82f6;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.tech-tag:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

/* 右侧登录区 */
.content-right {
  width: 480px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  z-index: 2;
  position: relative;
}

.login-form {
  width: 100%;
  max-width: 360px;
}

.form-header {
  text-align: center;
  margin-bottom: 40px;
}

.form-header h2 {
  font-size: 28px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
}

.form-header p {
  color: #64748b;
  font-size: 16px;
  margin: 0;
}

.login-form-content {
  margin-bottom: 24px;
}

.form-input {
  height: 48px;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  transition: all 0.3s ease;
}

.form-input:hover {
  border-color: #3b82f6;
}

.form-input:focus,
.form-input.ant-input-focused {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.login-button {
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  border: none;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.login-button:before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.login-button:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.4);
  background: linear-gradient(135deg, #2563eb, #0891b2);
}

.login-button:hover:before {
  left: 100%;
}

.login-button:active {
  transform: translateY(0) scale(0.98);
}


/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
    height: 100vh;
    min-height: 100vh;
  }

  /* 隐藏背景动画元素 */
  .particle-background,
  .grid-background,
  .floating-geometry {
    display: none;
  }

  .content-left {
    flex: none;
    height: auto;
    min-height: 200px;
    padding: 30px 20px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  }

  .content-right {
    flex: 1;
    width: 100%;
    padding: 30px 20px;
    min-height: calc(100vh - 200px);
  }

  /* 简化左侧内容 */
  .brand-section {
    max-width: 100%;
    text-align: center;
  }

  .logo-container {
    justify-content: center;
    margin-bottom: 20px;
    gap: 15px;
  }

  .logo-icon {
    width: 36px;
    height: 36px;
    margin-top: 0;
  }

  .cube-face {
    width: 36px;
    height: 36px;
    font-size: 14px;
  }

  .cube-face.front {
    transform: rotateY(0deg) translateZ(18px);
  }

  .cube-face.back {
    transform: rotateY(180deg) translateZ(18px);
  }

  .cube-face.right {
    transform: rotateY(90deg) translateZ(18px);
  }

  .cube-face.left {
    transform: rotateY(-90deg) translateZ(18px);
  }

  .cube-face.top {
    transform: rotateX(90deg) translateZ(18px);
  }

  .cube-face.bottom {
    transform: rotateX(-90deg) translateZ(18px);
  }

  .brand-title {
    align-items: center;
    gap: 8px;
  }

  .main-title {
    font-size: 36px;
  }

  .typewriter-container {
    min-width: auto;
    max-width: 100%;
    height: auto;
    justify-content: center;
  }

  .typewriter-text {
    font-size: 16px;
    text-align: center;
  }

  .cursor {
    font-size: 16px;
  }

  .brand-subtitle {
    font-size: 14px;
    margin-bottom: 20px;
  }

  /* 隐藏统计数据和技术标签以节省空间 */
  .stats-list,
  .tech-tags {
    display: none;
  }

  /* 登录表单优化 */
  .login-form {
    max-width: 100%;
  }

  .form-header {
    margin-bottom: 30px;
  }

  .form-header h2 {
    font-size: 24px;
  }

  .form-header p {
    font-size: 14px;
  }
}

/* 更小屏幕优化 */
@media (max-width: 480px) {
  .content-left {
    min-height: 150px;
    padding: 20px 15px;
  }

  .content-right {
    padding: 20px 15px;
    min-height: calc(100vh - 150px);
  }

  .main-title {
    font-size: 28px;
  }

  .typewriter-text {
    font-size: 14px;
  }

  .cursor {
    font-size: 14px;
  }

  .brand-subtitle {
    font-size: 12px;
  }

  .form-header h2 {
    font-size: 20px;
  }
}
</style>