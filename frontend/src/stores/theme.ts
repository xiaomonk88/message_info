import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'
export type AccentKey = 'ovh'

const STORAGE_KEY = 'ui.theme.ovh.v1'
const mql = window.matchMedia('(prefers-color-scheme: dark)')

export const ACCENTS: { key: AccentKey; label: string; swatch: string }[] = [
  { key: 'ovh', label: 'OVH 海洋蓝', swatch: '#0050d7' },
]

function readMode(): ThemeMode {
  const v = localStorage.getItem(STORAGE_KEY)
  return v === 'light' || v === 'dark' || v === 'system' ? v : 'light'
}

function applyTheme(dark: boolean) {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
}

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>(readMode())
  const accent = ref<AccentKey>('ovh')
  const systemDark = ref(mql.matches)

  mql.addEventListener('change', (e) => {
    systemDark.value = e.matches
  })

  const isDark = computed(() => (mode.value === 'system' ? systemDark.value : mode.value === 'dark'))

  watch(isDark, applyTheme, { immediate: true })
  watch(mode, (v) => localStorage.setItem(STORAGE_KEY, v))

  function setMode(v: ThemeMode) {
    mode.value = v
  }

  function toggle() {
    mode.value = isDark.value ? 'light' : 'dark'
  }

  function setAccent(v: AccentKey) {
    accent.value = v
  }

  return { mode, accent, isDark, setMode, setAccent, toggle }
})
