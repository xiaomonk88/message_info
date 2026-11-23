<template>
  <div class="login-page">
    <div class="login-top">
      <div class="login-brand">
        <span class="ovh-brand-mark" aria-hidden="true">
          <svg viewBox="0 0 28 24" fill="none">
            <path d="M2 5L9.5 20H14L6.5 5H2Z" fill="currentColor" />
            <path d="M12.5 5L17 14L21.5 5H26L18.5 20H15.5L10.5 10L12.5 5Z" fill="#0050D7" />
          </svg>
        </span>
        <span class="login-brand-name">Message_Info</span>
        <span class="login-console-pill">&gt; CONSOLE_</span>
      </div>

      <button
        class="icon-button"
        type="button"
        :aria-label="theme.isDark ? '切换到浅色' : '切换到深色'"
        @click="theme.toggle()"
      >
        <Sun v-if="theme.isDark" />
        <Moon v-else />
      </button>
    </div>

    <main class="auth-center">
      <div class="auth-card">
        <div class="auth-banner">
          <h1 class="auth-title">信息管理系统</h1>
        </div>

        <div class="auth-body">
          <div v-if="isRegister && !allowRegister && settingsLoaded" class="callout mb-0">
            <Lock />
            <div>
              <strong class="d-block">当前暂未开放自助注册</strong>
              <span>请联系系统管理员为您开通账号，或返回登录。</span>
            </div>
          </div>

          <form v-else class="auth-form" @submit.prevent="onSubmit">
            <div class="auth-field">
              <label class="form-label" for="loginUser">用户名</label>
              <input
                id="loginUser"
                v-model="form.username"
                type="text"
                class="form-control auth-input"
                :placeholder="isRegister ? '2–32 位，支持字母 / 数字 / 中文' : '请输入用户名'"
                autocomplete="username"
                autofocus
              />
            </div>

            <div v-if="isRegister" class="auth-field">
              <label class="form-label" for="regName">显示名称 <span class="label-opt">选填</span></label>
              <input
                id="regName"
                v-model="form.display_name"
                type="text"
                class="form-control auth-input"
                placeholder="例如：张三 / 运维组"
                maxlength="64"
              />
            </div>

            <div class="auth-field">
              <label class="form-label" for="loginPwd">密码</label>
              <div class="pwd-wrap">
                <input
                  id="loginPwd"
                  v-model="form.password"
                  :type="showPwd ? 'text' : 'password'"
                  class="form-control auth-input has-action"
                  :placeholder="isRegister ? '至少 6 位字符' : '请输入密码'"
                  :autocomplete="isRegister ? 'new-password' : 'current-password'"
                  @keyup.enter="onSubmit"
                />
                <button
                  type="button"
                  class="pwd-toggle"
                  :aria-label="showPwd ? '隐藏密码' : '显示密码'"
                  @click="showPwd = !showPwd"
                >
                  <EyeOff v-if="showPwd" /><Eye v-else />
                </button>
              </div>
            </div>

            <div v-if="isRegister" class="auth-field">
              <label class="form-label" for="regPwd2">确认密码</label>
              <input
                id="regPwd2"
                v-model="form.confirm"
                :type="showPwd ? 'text' : 'password'"
                class="form-control auth-input"
                :class="{ 'is-invalid': form.confirm && form.confirm !== form.password }"
                placeholder="请再次输入密码"
                autocomplete="new-password"
                @keyup.enter="onSubmit"
              />
            </div>

            <button type="submit" class="btn btn-primary btn-lg w-100 auth-submit" :disabled="loading">
              <span v-if="loading" class="spinner-border spinner-border-sm"></span>
              <template v-else>{{ isRegister ? '注册并进入控制台' : '登录控制台' }}</template>
            </button>
          </form>

          <div v-if="isRegister" class="auth-switch">
            已有账号？<RouterLink to="/login">返回登录</RouterLink>
          </div>
          <div v-else-if="allowRegister" class="auth-switch">
            还没有账号？<RouterLink to="/register">创建新账号</RouterLink>
          </div>
        </div>
      </div>
    </main>

    <footer class="login-foot">
      <span>© {{ year }} Message_Info Console</span>
      <span>·</span>
      <span>Fernet Encrypted Storage</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { Eye, EyeOff, Lock, Moon, Sun } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { authApi } from '@/api'
import { toast } from '@/utils/ui'

const form = reactive({ username: '', password: '', confirm: '', display_name: '' })
const loading = ref(false)
const showPwd = ref(false)
const auth = useAuthStore()
const theme = useThemeStore()
const router = useRouter()
const route = useRoute()
const isRegister = computed(() => route.path === '/register')
const allowRegister = ref(false)
const settingsLoaded = ref(false)
const year = new Date().getFullYear()

onMounted(async () => {
  try {
    const { data } = await authApi.settings()
    allowRegister.value = data.allow_register
  } finally {
    settingsLoaded.value = true
  }
})

watch(isRegister, () => {
  form.password = ''
  form.confirm = ''
})

async function onSubmit() {
  if (!form.username || !form.password) {
    toast('请填写用户名和密码', 'warning')
    return
  }
  if (isRegister.value) {
    if (form.password.length < 6) {
      toast('密码至少 6 位', 'warning')
      return
    }
    if (form.password !== form.confirm) {
      toast('两次输入的密码不一致', 'warning')
      return
    }
  }
  loading.value = true
  try {
    if (isRegister.value) {
      await auth.register(form.username.trim(), form.password, form.display_name.trim() || undefined)
      toast('注册成功，欢迎加入', 'success')
    } else {
      await auth.login(form.username.trim(), form.password)
    }
    router.push('/')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  min-height: 100svh;
  grid-template-rows: auto 1fr auto;
  background: var(--bg);
}

.login-top {
  display: flex;
  height: 54px;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--surface-border);
  background: var(--bg-topbar);
}

.login-brand {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: var(--ovh-navy);
}

.ovh-brand-mark {
  display: inline-flex;
  width: 28px;
  height: 24px;
}

.login-brand-name {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.login-console-pill {
  display: inline-flex;
  height: 22px;
  align-items: center;
  padding: 0 9px;
  border-radius: 999px;
  background: var(--ovh-navy);
  color: #ffffff;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
}

html[data-theme='dark'] .login-console-pill {
  background: var(--ovh-blue);
}

.auth-center {
  display: grid;
  place-items: center;
  padding: 32px 16px;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  overflow: hidden;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-xl);
  background: var(--bg-elev);
  box-shadow: var(--shadow-md);
}

.auth-banner {
  padding: 24px 28px 22px;
  border-bottom: 1px solid var(--hero-border);
  background: var(--hero-bg);
  text-align: center;
}

.auth-title {
  margin: 0;
  color: var(--hero-title);
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.auth-body {
  padding: 24px 28px 28px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.auth-field {
  display: flex;
  flex-direction: column;
}

.label-opt {
  margin-left: 4px;
  color: var(--text-faint);
  font-size: 12px;
  font-weight: 400;
}

.auth-input {
  height: 38px;
}

.auth-input.has-action {
  padding-right: 38px;
}

.pwd-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.pwd-toggle {
  position: absolute;
  right: 6px;
  display: inline-grid;
  width: 28px;
  height: 28px;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}

.pwd-toggle:hover {
  background: var(--ovh-ice);
  color: var(--ovh-blue);
}

.pwd-toggle .lucide {
  width: 15px;
  height: 15px;
}

.auth-submit {
  margin-top: 6px;
}

.auth-switch {
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid var(--hairline);
  color: var(--text-muted);
  font-size: 13px;
  text-align: center;
}

.auth-switch a {
  margin-left: 4px;
  color: var(--ovh-blue);
  font-weight: 600;
}

.login-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: var(--text-faint);
  font-size: 12px;
}
</style>
