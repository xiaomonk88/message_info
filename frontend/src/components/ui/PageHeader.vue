<template>
  <!-- 顶部横幅已移除：左侧导航已具备清晰选中态，首屏 100% 空间留给工具栏与数据表格 -->
</template>

<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  title?: string
  subtitle?: string
  eyebrow?: string
  icon?: Component
}>()
</script>
