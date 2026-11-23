<template>
  <div class="ske-table" aria-hidden="true">
    <div class="ske-row head">
      <Skeleton v-for="c in cols" :key="'h' + c" variant="line" :width="cellWidth(0, c)" height="10px" />
    </div>
    <div v-for="r in rows" :key="r" class="ske-row">
      <Skeleton v-for="c in cols" :key="c" variant="line" :width="cellWidth(r, c)" />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * SkeletonTable —— 表格首屏加载骨架。
 * 单元格宽度用确定性伪随机（避免每次渲染跳动）。
 */
import Skeleton from './Skeleton.vue'

withDefaults(
  defineProps<{
    rows?: number
    cols?: number
  }>(),
  { rows: 6, cols: 5 }
)

function cellWidth(r: number, c: number): string {
  return `${52 + ((r * 17 + c * 31) % 44)}%`
}
</script>

<style scoped>
.ske-table {
  padding: 4px 2px;
}

.ske-row {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  align-items: center;
  gap: 20px;
  padding: 13px 12px;
}

.ske-row + .ske-row {
  border-top: 1px solid var(--border-faint);
}

.ske-row.head {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
}
</style>
