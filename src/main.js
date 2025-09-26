import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import { useAuthStore } from './stores/auth'

// Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// Ant Design Vue 样式
import 'ant-design-vue/dist/reset.css'
// 全局样式
import './styles/global.css'

const app = createApp(App)

// 使用 Element Plus
app.use(ElementPlus)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用 Pinia 状态管理
const pinia = createPinia()
app.use(pinia)

// 使用路由
app.use(router)

// 初始化认证状态
const authStore = useAuthStore(pinia)
authStore.initAuth()

app.mount('#app')