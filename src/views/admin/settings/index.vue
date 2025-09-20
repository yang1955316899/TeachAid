<template>
  <div class="admin-settings">
    <div class="header">
      <h2>系统设置</h2>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="基础设置" name="basic">
        <el-form :model="basicSettings" label-width="120px" class="settings-form">
          <el-form-item label="系统名称">
            <el-input v-model="basicSettings.systemName" placeholder="请输入系统名称" />
          </el-form-item>
          <el-form-item label="系统描述">
            <el-input
              v-model="basicSettings.systemDescription"
              type="textarea"
              rows="3"
              placeholder="请输入系统描述"
            />
          </el-form-item>
          <el-form-item label="默认语言">
            <el-select v-model="basicSettings.defaultLanguage">
              <el-option label="中文" value="zh-CN" />
              <el-option label="English" value="en-US" />
            </el-select>
          </el-form-item>
          <el-form-item label="时区">
            <el-select v-model="basicSettings.timezone">
              <el-option label="UTC+8 (北京)" value="Asia/Shanghai" />
              <el-option label="UTC+0 (伦敦)" value="Europe/London" />
              <el-option label="UTC-5 (纽约)" value="America/New_York" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveBasicSettings" :loading="saving">
              保存设置
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="AI模型配置" name="ai">
        <el-form :model="aiSettings" label-width="120px" class="settings-form">
          <el-form-item label="主力视觉模型">
            <el-select v-model="aiSettings.primaryVisionModel">
              <el-option label="GPT-4V" value="gpt-4o" />
              <el-option label="Claude-3.5-Sonnet" value="claude-3-5-sonnet-20241022" />
              <el-option label="通义千问VL-Max" value="qwen-vl-max" />
            </el-select>
          </el-form-item>
          <el-form-item label="对话模型">
            <el-select v-model="aiSettings.chatModel">
              <el-option label="GPT-4O-Mini" value="gpt-4o-mini" />
              <el-option label="DeepSeek-Chat" value="deepseek-chat" />
              <el-option label="通义千问Turbo" value="qwen-turbo" />
            </el-select>
          </el-form-item>
          <el-form-item label="改写模型">
            <el-select v-model="aiSettings.rewriteModel">
              <el-option label="Claude-3.5-Sonnet" value="claude-3-5-sonnet-20241022" />
              <el-option label="Yi-Large" value="yi-large" />
              <el-option label="Moonshot-v1-8k" value="moonshot-v1-8k" />
            </el-select>
          </el-form-item>
          <el-form-item label="启用智能切换">
            <el-switch v-model="aiSettings.enableSmartSwitch" />
            <small>当主模型不可用时自动切换到备用模型</small>
          </el-form-item>
          <el-form-item label="月度预算限制">
            <el-input-number
              v-model="aiSettings.monthlyBudget"
              :min="0"
              :max="10000"
              :step="100"
            />
            <small>单位：美元</small>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveAiSettings" :loading="saving">
              保存设置
            </el-button>
            <el-button @click="testAiConnection">测试连接</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="文件上传设置" name="upload">
        <el-form :model="uploadSettings" label-width="120px" class="settings-form">
          <el-form-item label="最大文件大小">
            <el-input-number
              v-model="uploadSettings.maxFileSize"
              :min="1"
              :max="100"
              :step="1"
            />
            <small>单位：MB</small>
          </el-form-item>
          <el-form-item label="允许的文件类型">
            <el-checkbox-group v-model="uploadSettings.allowedTypes">
              <el-checkbox label="image/jpeg">JPEG</el-checkbox>
              <el-checkbox label="image/png">PNG</el-checkbox>
              <el-checkbox label="image/webp">WebP</el-checkbox>
              <el-checkbox label="application/pdf">PDF</el-checkbox>
              <el-checkbox label="text/plain">TXT</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          <el-form-item label="自动处理">
            <el-switch v-model="uploadSettings.autoProcess" />
            <small>上传后自动提取题目内容</small>
          </el-form-item>
          <el-form-item label="存储路径">
            <el-input v-model="uploadSettings.storagePath" placeholder="/uploads/" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveUploadSettings" :loading="saving">
              保存设置
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="邮件通知" name="email">
        <el-form :model="emailSettings" label-width="120px" class="settings-form">
          <el-form-item label="SMTP服务器">
            <el-input v-model="emailSettings.smtpHost" placeholder="smtp.example.com" />
          </el-form-item>
          <el-form-item label="SMTP端口">
            <el-input-number v-model="emailSettings.smtpPort" :min="1" :max="65535" />
          </el-form-item>
          <el-form-item label="用户名">
            <el-input v-model="emailSettings.username" placeholder="your-email@example.com" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="emailSettings.password" type="password" show-password />
          </el-form-item>
          <el-form-item label="发件人名称">
            <el-input v-model="emailSettings.fromName" placeholder="TeachAid系统" />
          </el-form-item>
          <el-form-item label="启用SSL">
            <el-switch v-model="emailSettings.useSSL" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveEmailSettings" :loading="saving">
              保存设置
            </el-button>
            <el-button @click="testEmail">发送测试邮件</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="缓存设置" name="cache">
        <el-form :model="cacheSettings" label-width="120px" class="settings-form">
          <el-form-item label="Redis地址">
            <el-input v-model="cacheSettings.redisUrl" placeholder="redis://localhost:6379" />
          </el-form-item>
          <el-form-item label="缓存TTL">
            <el-input-number
              v-model="cacheSettings.defaultTTL"
              :min="60"
              :max="86400"
              :step="60"
            />
            <small>单位：秒</small>
          </el-form-item>
          <el-form-item label="启用语义缓存">
            <el-switch v-model="cacheSettings.enableSemanticCache" />
            <small>基于语义相似度的智能缓存</small>
          </el-form-item>
          <el-form-item label="相似度阈值">
            <el-slider
              v-model="cacheSettings.similarityThreshold"
              :min="0.5"
              :max="1.0"
              :step="0.05"
              :disabled="!cacheSettings.enableSemanticCache"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveCacheSettings" :loading="saving">
              保存设置
            </el-button>
            <el-button @click="clearCache" type="warning">清空缓存</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeTab = ref('basic')
const saving = ref(false)

const basicSettings = reactive({
  systemName: 'TeachAid',
  systemDescription: 'AI辅助教学平台',
  defaultLanguage: 'zh-CN',
  timezone: 'Asia/Shanghai'
})

const aiSettings = reactive({
  primaryVisionModel: 'gpt-4o',
  chatModel: 'gpt-4o-mini',
  rewriteModel: 'claude-3-5-sonnet-20241022',
  enableSmartSwitch: true,
  monthlyBudget: 1000
})

const uploadSettings = reactive({
  maxFileSize: 10,
  allowedTypes: ['image/jpeg', 'image/png', 'application/pdf'],
  autoProcess: true,
  storagePath: '/uploads/'
})

const emailSettings = reactive({
  smtpHost: '',
  smtpPort: 587,
  username: '',
  password: '',
  fromName: 'TeachAid系统',
  useSSL: true
})

const cacheSettings = reactive({
  redisUrl: 'redis://localhost:6379',
  defaultTTL: 3600,
  enableSemanticCache: true,
  similarityThreshold: 0.85
})

const saveBasicSettings = async () => {
  saving.value = true
  try {
    // TODO: 调用API保存基础设置
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('基础设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const saveAiSettings = async () => {
  saving.value = true
  try {
    // TODO: 调用API保存AI设置
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('AI模型配置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const testAiConnection = async () => {
  try {
    // TODO: 测试AI模型连接
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('AI模型连接测试成功')
  } catch (error) {
    ElMessage.error('连接测试失败')
  }
}

const saveUploadSettings = async () => {
  saving.value = true
  try {
    // TODO: 调用API保存上传设置
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('文件上传设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const saveEmailSettings = async () => {
  saving.value = true
  try {
    // TODO: 调用API保存邮件设置
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('邮件通知设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const testEmail = async () => {
  try {
    // TODO: 发送测试邮件
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('测试邮件发送成功')
  } catch (error) {
    ElMessage.error('测试邮件发送失败')
  }
}

const saveCacheSettings = async () => {
  saving.value = true
  try {
    // TODO: 调用API保存缓存设置
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('缓存设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const clearCache = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有缓存吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    // TODO: 清空缓存
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('缓存清空成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清空缓存失败')
    }
  }
}

onMounted(() => {
  // TODO: 加载现有设置
})
</script>

<style scoped>
.admin-settings {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.settings-form {
  max-width: 600px;
  padding: 20px;
}

.settings-form .el-form-item {
  margin-bottom: 22px;
}

.settings-form small {
  margin-left: 10px;
  color: #999;
}
</style>