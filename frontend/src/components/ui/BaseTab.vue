<template>
  <div>
    <ul class="nav nav-tabs mb-3">
      <li v-for="t in tabs" :key="t.name" class="nav-item">
        <button
          type="button"
          class="nav-link"
          :class="{ active: t.name === active }"
          @click="select(t.name)"
        >
          {{ t.label }}
          <span v-if="t.badge !== undefined && t.badge !== null && t.badge !== ''" class="tab-badge">{{ t.badge }}</span>
        </button>
      </li>
    </ul>
    <div class="tab-content">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { provide, reactive, ref, watch } from 'vue'

interface TabMeta {
  name: string
  label: string
  badge?: string | number | null
}

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [string] }>()

const tabs = reactive<TabMeta[]>([])
const active = ref(props.modelValue)

watch(
  () => props.modelValue,
  (v) => (active.value = v)
)

function select(name: string) {
  active.value = name
  emit('update:modelValue', name)
}

provide('baseTab', {
  active,
  // meta 为 TabPane 的响应式 props，label / badge 变化会同步到标签栏
  register(meta: TabMeta) {
    if (!tabs.find((t) => t.name === meta.name)) tabs.push(meta)
    if (!active.value) active.value = meta.name
  },
  unregister(name: string) {
    const i = tabs.findIndex((t) => t.name === name)
    if (i >= 0) tabs.splice(i, 1)
  },
})
</script>
