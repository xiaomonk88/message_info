<template>
  <div class="icon-picker">
    <button type="button" class="ip-trigger" :class="{ open }" @click="open = !open">
      <span class="ip-current">
        <AppIcon :name="modelValue" :fallback="fallback" />
      </span>
      <span class="ip-name" :class="{ 'is-default': !modelValue }">
        {{ modelValue || '默认图标' }}
      </span>
      <span class="ip-actions">
        <span v-if="modelValue" class="ip-clear" role="button" title="清除图标" @click.stop="clear">
          <X />
        </span>
        <ChevronDown class="ip-caret" :class="{ open }" />
      </span>
    </button>

    <div v-if="open" class="ip-panel">
      <input
        v-model="q"
        type="text"
        class="form-control form-control-sm ip-search"
        placeholder="搜索图标（中文 / 英文名）"
      />
      <div class="ip-scroll">
        <template v-for="g in filteredGroups" :key="g.label">
          <div class="ip-group-label">{{ g.label }}</div>
          <div class="ip-grid">
            <button
              v-for="d in g.items"
              :key="d.name"
              type="button"
              class="ip-cell"
              :class="{ active: d.name === modelValue }"
              :title="d.name"
              @click="pick(d.name)"
            >
              <component :is="d.icon" />
            </button>
          </div>
        </template>
        <div v-if="!filteredGroups.length" class="ip-empty">没有匹配的图标</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * IconPicker —— 分类/板块图标选择器。
 * inline 渲染（不 teleport），保持在 BaseModal 的 focustrap 内。
 * v-model 值为 lucide PascalCase 图标名；清除时 emit null。
 */
import { computed, ref } from 'vue'
import { ChevronDown, X } from 'lucide-vue-next'
import { ICON_LIST } from '@/components/icons/registry'
import AppIcon from '@/components/AppIcon.vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string | null
    fallback?: string
  }>(),
  { modelValue: null, fallback: 'Database' }
)

const emit = defineEmits<{ 'update:modelValue': [string | null] }>()

const open = ref(false)
const q = ref('')

const filteredGroups = computed(() => {
  const kw = q.value.trim().toLowerCase()
  const list = kw
    ? ICON_LIST.filter(
        (d) => d.name.toLowerCase().includes(kw) || d.kw.toLowerCase().includes(kw)
      )
    : ICON_LIST
  const groups: { label: string; items: typeof ICON_LIST }[] = []
  for (const d of list) {
    let g = groups.find((x) => x.label === d.group)
    if (!g) {
      g = { label: d.group, items: [] }
      groups.push(g)
    }
    g.items.push(d)
  }
  return groups
})

function pick(name: string) {
  emit('update:modelValue', name)
  open.value = false
}

function clear() {
  emit('update:modelValue', null)
}
</script>

<style scoped>
.ip-trigger {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: var(--bg-elev);
  text-align: left;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.ip-trigger:hover {
  border-color: var(--ink-300);
}

.ip-trigger.open {
  border-color: var(--accent);
}

.ip-trigger.open {
  box-shadow: var(--accent-ring);
}

.ip-current {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  border-radius: 8px;
  background: var(--accent);
  color: var(--on-accent);
}

.ip-current .lucide {
  width: 16px;
  height: 16px;
}

.ip-name {
  flex: 1 1 auto;
  overflow: hidden;
  font-size: 12px;
  color: var(--text);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ip-name.is-default {
  color: var(--text-muted);
}

.ip-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.ip-clear {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  color: var(--text-muted);
}

.ip-clear:hover {
  background: var(--danger-soft);
  color: var(--danger);
}

.ip-clear .lucide {
  width: 13px;
  height: 13px;
}

.ip-caret {
  width: 15px;
  height: 15px;
  color: var(--text-muted);
  transition: transform 0.18s ease;
}

.ip-caret.open {
  transform: rotate(180deg);
}

.ip-panel {
  margin-top: 8px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-elev);
  box-shadow: var(--shadow-sm);
}

.ip-search {
  margin-bottom: 8px;
}

.ip-scroll {
  max-height: 240px;
  overflow-y: auto;
}

.ip-group-label {
  padding: 8px 4px 4px;
  color: var(--text-faint);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.ip-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 4px;
}

.ip-cell {
  display: grid;
  place-items: center;
  aspect-ratio: 1;
  border: 1px solid transparent;
  border-radius: var(--radius);
  background: transparent;
  color: var(--text-soft);
  cursor: pointer;
  transition: background 0.12s ease, color 0.12s ease;
}

.ip-cell:hover {
  background: var(--bg-soft);
  color: var(--text);
}

.ip-cell.active {
  border-color: var(--accent);
  background: var(--accent);
  color: var(--on-accent);
}

.ip-cell .lucide {
  width: 17px;
  height: 17px;
}

.ip-empty {
  padding: 24px 0;
  color: var(--text-muted);
  font-size: 11.5px;
  text-align: center;
}

@media (max-width: 576px) {
  .ip-grid {
    grid-template-columns: repeat(6, 1fr);
  }
}
</style>
