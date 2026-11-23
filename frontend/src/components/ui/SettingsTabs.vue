<template>
  <nav v-if="items.length > 1" class="sub-tabs" aria-label="系统设置导航">
    <RouterLink
      v-for="item in items"
      :key="item.to"
      :to="item.to"
      class="sub-tab"
      :class="{ active: route.path === item.to }"
    >
      <component :is="item.icon" class="sub-tab-ico" />
      <span>{{ item.label }}</span>
    </RouterLink>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { systemNavFor } from '@/config/nav'

const route = useRoute()
const auth = useAuthStore()

const items = computed(() => systemNavFor(auth.isAdmin).filter((item) => item.group === 'ops'))
</script>

<style scoped>
.sub-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 18px;
  border-bottom: 1px solid var(--surface-border);
  overflow-x: auto;
  scrollbar-width: none;
}

.sub-tabs::-webkit-scrollbar {
  display: none;
}

.sub-tab {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 14px 11px;
  margin-bottom: -1px;
  border-bottom: 2px solid transparent;
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  text-decoration: none;
  transition: color 0.14s ease, border-color 0.14s ease;
}

.sub-tab:hover {
  color: var(--ovh-navy);
}

.sub-tab.active {
  border-bottom-color: var(--ovh-blue);
  color: var(--ovh-navy);
  font-weight: 600;
}

.sub-tab-ico {
  width: 15px;
  height: 15px;
  color: var(--text-faint);
}

.sub-tab.active .sub-tab-ico {
  color: var(--ovh-blue);
}
</style>
