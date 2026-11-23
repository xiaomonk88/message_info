<template>
  <div v-show="ctx.active.value === name" class="tab-pane fade" :class="{ 'show active': ctx.active.value === name }">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { inject, onBeforeUnmount, onMounted, type Ref } from 'vue'

const props = defineProps<{ name: string; label: string; badge?: string | number | null }>()

interface TabCtx {
  active: Ref<string>
  register: (m: { name: string; label: string; badge?: string | number | null }) => void
  unregister: (name: string) => void
}

const ctx = inject<TabCtx>('baseTab')!

onMounted(() => ctx.register(props))
onBeforeUnmount(() => ctx.unregister(props.name))
</script>
