<template>
  <div class="ovh-pager">
    <select
      v-if="pageSizes && pageSizes.length"
      class="form-select form-select-sm ovh-pager-size"
      :value="pageSize"
      aria-label="每页条数"
      @change="onSizeChange"
    >
      <option v-for="s in pageSizes" :key="s" :value="s">{{ s }}</option>
    </select>
    <span class="ovh-pager-info">共 {{ total }} 条</span>
    <nav aria-label="分页导航">
      <ul class="pagination pagination-sm mb-0">
        <li class="page-item" :class="{ disabled: page <= 1 }">
          <button class="page-link" type="button" @click="go(page - 1)"><ChevronLeft /></button>
        </li>
        <li
          v-for="p in pageItems"
          :key="p.key"
          class="page-item"
          :class="{ active: p.num === page, disabled: p.num === null }"
        >
          <span v-if="p.num === null" class="page-link">…</span>
          <button v-else class="page-link" type="button" @click="go(p.num)">{{ p.num }}</button>
        </li>
        <li class="page-item" :class="{ disabled: page >= totalPages }">
          <button class="page-link" type="button" @click="go(page + 1)"><ChevronRight /></button>
        </li>
      </ul>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    total: number
    page: number
    pageSize: number
    pageSizes?: number[]
  }>(),
  { pageSizes: () => [] }
)

const emit = defineEmits<{
  'update:page': [number]
  'update:pageSize': [number]
}>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

const pageItems = computed(() => {
  const tp = totalPages.value
  const cur = props.page
  const items: { key: string; num: number | null }[] = []
  const push = (n: number | null, key?: string) => items.push({ key: key ?? `p${n}`, num: n })
  const range: number[] = []
  for (let i = Math.max(1, cur - 2); i <= Math.min(tp, cur + 2); i++) range.push(i)
  if (range[0] > 1) {
    push(1)
    if (range[0] > 2) push(null, 'l-ellipsis')
  }
  range.forEach((n) => push(n))
  if (range[range.length - 1] < tp) {
    if (range[range.length - 1] < tp - 1) push(null, 'r-ellipsis')
    push(tp)
  }
  return items
})

function go(p: number) {
  if (p < 1 || p > totalPages.value || p === props.page) return
  emit('update:page', p)
}

function onSizeChange(e: Event) {
  emit('update:pageSize', Number((e.target as HTMLSelectElement).value))
}
</script>

<style scoped>
.ovh-pager {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.ovh-pager-size {
  width: auto;
  min-width: 66px;
}

.ovh-pager-info {
  color: var(--text-muted);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}
</style>
