import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi, type TokenOut, type UserRole } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const username = ref<string>(localStorage.getItem('username') || '')
  const role = ref<UserRole>((localStorage.getItem('role') as UserRole) || 'member')
  const userId = ref<number | null>(null)
  const displayName = ref<string>('')

  const isAdmin = computed(() => role.value === 'admin')

  function applyToken(data: TokenOut) {
    token.value = data.access_token
    username.value = data.username
    role.value = data.role
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    localStorage.setItem('role', data.role)
  }

  async function login(u: string, p: string) {
    const { data } = await authApi.login(u, p)
    applyToken(data)
    await fetchMe()
  }

  async function register(u: string, p: string, display_name?: string) {
    const { data } = await authApi.register({ username: u, password: p, display_name })
    applyToken(data)
    await fetchMe()
  }

  /** 以服务端为准刷新角色（防止本地缓存的角色过期，例如被管理员降级） */
  async function fetchMe() {
    if (!token.value) return
    const { data } = await authApi.me()
    userId.value = data.id
    username.value = data.username
    displayName.value = data.display_name || ''
    role.value = data.role
    localStorage.setItem('username', data.username)
    localStorage.setItem('role', data.role)
  }

  function logout() {
    token.value = ''
    username.value = ''
    role.value = 'member'
    userId.value = null
    displayName.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
  }

  return { token, username, role, userId, displayName, isAdmin, login, register, fetchMe, logout }
})
