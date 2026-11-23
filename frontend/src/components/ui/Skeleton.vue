<template>
  <span class="ske" :class="variant" :style="sizeStyle" aria-hidden="true"></span>
</template>

<script setup lang="ts">
/**
 * Skeleton —— 骨架占位原语（shimmer 动画）。
 * variant: line（文本行）/ rect（块面）/ circle（圆）
 */
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    variant?: 'line' | 'rect' | 'circle'
    width?: string
    height?: string
  }>(),
  { variant: 'line', width: '', height: '' }
)

const sizeStyle = computed(() => {
  const s: Record<string, string> = {}
  if (props.width) s.width = props.width
  if (props.height) s.height = props.height
  return s
})
</script>

<style scoped>
.ske {
  display: block;
  border-radius: 6px;
  background: linear-gradient(90deg, var(--bg-subtle) 25%, var(--bg-soft) 45%, var(--bg-subtle) 65%);
  background-size: 200% 100%;
  animation: ske-shimmer 1.4s ease-in-out infinite;
}

.ske.line {
  width: 100%;
  height: 12px;
}

.ske.rect {
  width: 100%;
  height: 84px;
  border-radius: var(--radius);
}

.ske.circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
}

@keyframes ske-shimmer {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ske {
    animation: none;
  }
}
</style>
