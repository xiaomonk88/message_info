<template>
  <component :is="iconComp" />
</template>

<script setup lang="ts">
/**
 * AppIcon —— 按存库字符串渲染 lucide 图标，全站统一入口。
 * name 为空或不在注册表内时回退 fallback。
 */
import { computed } from 'vue'
import { resolveIcon } from '@/components/icons/registry'

const props = withDefaults(
  defineProps<{
    name?: string | null
    fallback?: string
  }>(),
  { name: '', fallback: 'Database' }
)

const iconComp = computed(() => resolveIcon(props.name, props.fallback))
</script>
