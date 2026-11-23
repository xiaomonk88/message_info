<template>
  <teleport to="body">
    <transition name="cp-fade">
      <div v-if="modelValue" class="cp-overlay" @mousedown.self="close">
        <div class="cp-panel" role="dialog" aria-modal="true" aria-label="快速导航">
          <div class="cp-input-row">
            <Search class="cp-search-ico" />
            <input
              ref="inputEl"
              v-model="query"
              class="cp-input"
              type="text"
              placeholder="搜索板块、页面…"
              @keydown="onKeydown"
            />
            <kbd class="cp-kbd">Esc</kbd>
          </div>
          <div ref="listEl" class="cp-list">
            <template v-for="group in groupedResults" :key="group.label">
              <div class="cp-group-label">{{ group.label }}</div>
              <button
                v-for="item in group.items"
                :key="item.key"
                type="button"
                class="cp-item"
                :class="{ active: item.flatIndex === activeIndex }"
                :data-cp-index="item.flatIndex"
                @click="go(item)"
                @mouseenter="activeIndex = item.flatIndex"
              >
                <span class="cp-item-ico"><component :is="item.icon" /></span>
                <span class="cp-item-label">{{ item.label }}</span>
                <span v-if="item.hint" class="cp-item-hint">{{ item.hint }}</span>
                <CornerDownLeft v-if="item.flatIndex === activeIndex" class="cp-enter-ico" />
              </button>
            </template>
            <div v-if="!flatResults.length" class="cp-empty">
              <SearchX />
              <span>没有匹配的结果</span>
            </div>
          </div>
          <div class="cp-foot">
            <span><kbd class="cp-kbd">↑</kbd><kbd class="cp-kbd">↓</kbd> 切换</span>
            <span><kbd class="cp-kbd">Enter</kbd> 打开</span>
            <span><kbd class="cp-kbd">Esc</kbd> 关闭</span>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Component } from 'vue'
import { CornerDownLeft, LayoutGrid, Search, SearchX } from 'lucide-vue-next'
import { useNavStore } from '@/stores/nav'
import { systemNavFor } from '@/config/nav'
import { useAuthStore } from '@/stores/auth'
import { resolveIcon } from '@/components/icons/registry'

interface PaletteItem {
  key: string
  group: string
  label: string
  hint?: string
  keywords?: string
  icon: Component
  to: string
  flatIndex: number
}

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()

const route = useRoute()
const router = useRouter()
const nav = useNavStore()
const auth = useAuthStore()

const query = ref('')
const activeIndex = ref(0)
const inputEl = ref<HTMLInputElement>()
const listEl = ref<HTMLElement>()

const allItems = computed<Omit<PaletteItem, 'flatIndex'>[]>(() => {
  const catName = (id: number | null | undefined) =>
    nav.categories.find((c) => c.id === id)?.name || ''
  return [
    { key: 'p-dashboard', group: '页面', label: '概览', icon: LayoutGrid, to: '/dashboard' },
    ...nav.modules.map((m) => ({
      key: `m-${m.id}`,
      group: '板块',
      label: m.name,
      hint: catName(m.category_id) || '未分类',
      keywords: `${m.code || ''} ${catName(m.category_id)}`,
      icon: resolveIcon(m.icon),
      to: `/m/${m.id}`,
    })),
    ...systemNavFor(auth.isAdmin).map((s) => ({
      key: `s-${s.to}`,
      group: '系统',
      label: s.label,
      hint: s.desc,
      icon: s.icon,
      to: s.to,
    })),
  ]
})

function score(text: string | undefined, q: string): number {
  if (!text) return 0
  const t = text.toLowerCase()
  if (t.startsWith(q)) return 3
  if (t.includes(q)) return 2
  let i = 0
  for (const ch of t) {
    if (ch === q[i]) i++
    if (i === q.length) return 1
  }
  return 0
}

const flatResults = computed<PaletteItem[]>(() => {
  const q = query.value.trim().toLowerCase()
  let list = allItems.value
  if (q) {
    list = list
      .map((item, idx) => ({
        item,
        idx,
        s: Math.max(score(item.label, q), score(item.hint, q), score(item.keywords, q)),
      }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s || a.idx - b.idx)
      .map((x) => x.item)
  }
  const order = ['页面', '板块', '系统']
  const flat: PaletteItem[] = []
  for (const g of order) {
    for (const item of list.filter((i) => i.group === g)) {
      flat.push({ ...item, flatIndex: flat.length })
    }
  }
  return flat
})

const groupedResults = computed(() => {
  const groups: { label: string; items: PaletteItem[] }[] = []
  for (const item of flatResults.value) {
    let g = groups.find((x) => x.label === item.group)
    if (!g) {
      g = { label: item.group, items: [] }
      groups.push(g)
    }
    g.items.push(item)
  }
  return groups
})

watch(flatResults, () => {
  activeIndex.value = 0
})

watch(
  () => props.modelValue,
  async (open) => {
    document.body.classList.toggle('no-scroll', open)
    if (open) {
      query.value = ''
      activeIndex.value = 0
      await nextTick()
      inputEl.value?.focus()
    }
  }
)

watch(
  () => route.path,
  () => close()
)

function close() {
  emit('update:modelValue', false)
}

function go(item: PaletteItem) {
  close()
  if (route.path !== item.to) router.push(item.to)
}

function move(delta: number) {
  const n = flatResults.value.length
  if (!n) return
  activeIndex.value = (activeIndex.value + delta + n) % n
  nextTick(() => {
    listEl.value
      ?.querySelector(`[data-cp-index="${activeIndex.value}"]`)
      ?.scrollIntoView({ block: 'nearest' })
  })
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    move(1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    move(-1)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const item = flatResults.value[activeIndex.value]
    if (item) go(item)
  } else if (e.key === 'Escape') {
    e.preventDefault()
    close()
  }
}

function onGlobalKeydown(e: KeyboardEvent) {
  if (((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') || (e.altKey && e.key.toLowerCase() === 's')) {
    if (!props.modelValue && document.querySelector('.modal.show, .offcanvas.show')) return
    e.preventDefault()
    emit('update:modelValue', !props.modelValue)
  } else if (e.key === 'Escape' && props.modelValue) {
    close()
  }
}

onMounted(() => window.addEventListener('keydown', onGlobalKeydown))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKeydown)
  if (props.modelValue) document.body.classList.remove('no-scroll')
})
</script>

<style scoped>
.cp-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 14vh 16px 16px;
  background: var(--bg-overlay);
  backdrop-filter: blur(2px);
}

.cp-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 560px;
  max-height: 66vh;
  overflow: hidden;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-xl);
  background: var(--bg-elev-strong);
  box-shadow: var(--shadow-xl);
}

.cp-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--hairline);
}

.cp-search-ico {
  width: 16px;
  height: 16px;
  color: var(--text-muted);
}

.cp-input {
  flex: 1 1 auto;
  min-width: 0;
  border: 0;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: var(--text);
}

.cp-input::placeholder {
  color: var(--text-faint);
}

.cp-list {
  flex: 1 1 auto;
  overflow-y: auto;
  padding: 6px;
}

.cp-group-label {
  padding: 8px 10px 4px;
  color: var(--text-faint);
  font-size: 12px;
  font-weight: 500;
}

.cp-item {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--text-soft);
  font-size: 14px;
  text-align: left;
  cursor: pointer;
}

.cp-item.active {
  background: var(--bg-subtle);
  color: var(--text);
}

.cp-item-ico {
  display: inline-grid;
  place-items: center;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  color: var(--text-muted);
}

.cp-item.active .cp-item-ico {
  color: var(--text);
}

.cp-item-ico .lucide {
  width: 15px;
  height: 15px;
}

.cp-item-label {
  flex-shrink: 0;
  font-weight: 500;
  color: var(--text);
}

.cp-item-hint {
  flex: 1 1 auto;
  overflow: hidden;
  color: var(--text-faint);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cp-enter-ico {
  width: 13px;
  height: 13px;
  flex-shrink: 0;
  color: var(--text-muted);
}

.cp-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 0;
  color: var(--text-muted);
  font-size: 12.5px;
}

.cp-empty .lucide {
  width: 24px;
  height: 24px;
  color: var(--text-faint);
}

.cp-foot {
  display: flex;
  gap: 14px;
  padding: 9px 16px;
  border-top: 1px solid var(--hairline);
  background: var(--bg-soft);
  color: var(--text-faint);
  font-size: 11.5px;
}

.cp-foot span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.cp-kbd {
  display: inline-block;
  min-width: 18px;
  padding: 1px 5px;
  border: 1px solid var(--surface-border);
  border-radius: 5px;
  background: var(--bg-elev);
  color: var(--text-muted);
  font-family: var(--font-sans);
  font-size: 10.5px;
  line-height: 1.4;
  text-align: center;
}

.cp-fade-enter-active {
  transition: opacity 0.14s ease;
}

.cp-fade-enter-active .cp-panel {
  transition: transform 0.16s ease;
}

.cp-fade-leave-active {
  transition: opacity 0.1s ease;
}

.cp-fade-enter-from,
.cp-fade-leave-to {
  opacity: 0;
}

.cp-fade-enter-from .cp-panel {
  transform: translateY(-6px) scale(0.99);
}
</style>
