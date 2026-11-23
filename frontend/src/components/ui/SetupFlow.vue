<template>
  <nav class="sub-tabs" aria-label="数据建模导航">
    <RouterLink
      v-for="(step, i) in steps"
      :key="step.to"
      :to="step.to"
      class="sub-tab"
      :class="{ active: route.path === step.to }"
    >
      <span class="sub-tab-num">{{ i + 1 }}</span>
      <span>{{ step.label }}</span>
    </RouterLink>
  </nav>
</template>

<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'
import { SYSTEM_NAV } from '@/config/nav'

const route = useRoute()
const steps = SYSTEM_NAV.filter((item) => item.group === 'structure')
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
  position: relative;
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

.sub-tab-num {
  display: inline-grid;
  width: 20px;
  height: 20px;
  place-items: center;
  border-radius: 50%;
  background: var(--bg-subtle);
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.sub-tab.active .sub-tab-num {
  background: var(--ovh-blue);
  color: #ffffff;
}
</style>
