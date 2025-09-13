import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import { useAuthStore } from './stores/auth'

// Ant Design Vue 样式
import 'ant-design-vue/dist/reset.css'

const app = createApp(App)

// 使用 Pinia 状态管理
const pinia = createPinia()
app.use(pinia)

// 使用路由
app.use(router)

// 初始化认证状态
const authStore = useAuthStore(pinia)
authStore.initAuth()

app.mount('#app')