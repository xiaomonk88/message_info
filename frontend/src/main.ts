import { createApp } from 'vue'
import { createPinia } from 'pinia'

// 样式顺序很关键：字体 → Bootstrap → 本地令牌与设计系统覆盖
import './styles/fonts.css'
import 'bootstrap/dist/css/bootstrap.min.css'
import './styles/main.css'

import App from './App.vue'
import router from './router'
import { useThemeStore } from '@/stores/theme'
import { vLoading } from '@/components/ui/loading'
import { vTip } from '@/components/ui/tooltip'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// 尽早应用主题，避免首屏闪白
useThemeStore(pinia)

app.directive('loading', vLoading)
app.directive('tip', vTip)

app.mount('#app')
