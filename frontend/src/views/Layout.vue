<template>
  <div class="ovh-shell" :class="{ 'is-collapsed': isCollapsed, 'is-mobile-open': mobileOpen }">
    <!-- ================= 顶部纯白通栏导航（OVHcloud Console Header） ================= -->
    <header class="ovh-topbar">
      <div class="ovh-topbar-left">
        <button
          v-if="isMobile"
          class="top-icon-btn"
          type="button"
          aria-label="打开菜单"
          @click="mobileOpen = true"
        >
          <Menu />
        </button>

        <RouterLink to="/dashboard" class="ovh-brand" aria-label="Message_Info Console">
          <span class="ovh-brand-mark" aria-hidden="true">
            <svg viewBox="0 0 28 24" fill="none">
              <path d="M2 5L9.5 20H14L6.5 5H2Z" fill="currentColor" />
              <path d="M12.5 5L17 14L21.5 5H26L18.5 20H15.5L10.5 10L12.5 5Z" fill="#0050D7" />
            </svg>
          </span>
          <span class="ovh-brand-name">Message_Info</span>
          <span class="ovh-console-pill d-none d-sm-inline-flex">&gt; CONSOLE_</span>
        </RouterLink>
      </div>

      <div class="ovh-topbar-right">
        <button
          class="top-icon-btn"
          type="button"
          v-tip:bottom="'全局检索 (⌘K)'"
          aria-label="快速搜索"
          @click="paletteOpen = true"
        >
          <Search />
        </button>

        <button
          class="top-icon-btn"
          type="button"
          v-tip:bottom="theme.isDark ? '切换浅色控制台' : '切换深色控制台'"
          :aria-label="theme.isDark ? '切换浅色' : '切换深色'"
          @click="theme.toggle()"
        >
          <Sun v-if="theme.isDark" />
          <Moon v-else />
        </button>

        <!-- 右上角圆形用户徽标（复刻 OVH XL 圆形头像） -->
        <div ref="userMenuEl" class="ovh-user-wrap">
          <button
            class="ovh-avatar-btn"
            type="button"
            aria-haspopup="menu"
            :aria-expanded="userMenuOpen"
            :title="auth.username || '管理员'"
            @click="userMenuOpen = !userMenuOpen"
          >
            {{ userInitials }}
          </button>

          <transition name="pop">
            <div v-if="userMenuOpen" class="ovh-user-menu" role="menu">
              <div class="ovh-user-head">
                <span class="ovh-avatar-sm">{{ userInitials }}</span>
                <div class="ovh-user-meta">
                  <div class="ovh-user-name">{{ auth.username || '管理员' }}</div>
                  <div class="ovh-user-role">{{ roleLabel }}</div>
                </div>
              </div>
              <div class="ovh-menu-sep"></div>
              <RouterLink to="/admin/account" class="ovh-menu-item" role="menuitem" @click="userMenuOpen = false">
                <ShieldCheck />账号安全设置
              </RouterLink>
              <RouterLink v-if="auth.isAdmin" to="/admin/backups" class="ovh-menu-item" role="menuitem" @click="userMenuOpen = false">
                <Archive />数据快照与备份
              </RouterLink>
              <div class="ovh-menu-sep"></div>
              <button class="ovh-menu-item is-danger" type="button" role="menuitem" @click="onLogout">
                <LogOut />退出登录
              </button>
            </div>
          </transition>
        </div>
      </div>
    </header>

    <!-- ================= 下方主体：纯白左栏 + 纯白无界主工作区 ================= -->
    <div class="ovh-body">
      <aside class="ovh-sidebar">
        <!-- 顶部：OVH 双胶囊切换器 (业务板块 | 系统管理) -->
        <div v-if="expanded" class="sb-top-ctrl">
          <div class="ovh-dual-pills" role="tablist">
            <button
              type="button"
              class="ovh-dual-pill"
              :class="{ active: sbMode === 'modules' }"
              @click="sbMode = 'modules'"
            >
              业务板块
            </button>
            <button
              type="button"
              class="ovh-dual-pill"
              :class="{ active: sbMode === 'admin' }"
              @click="sbMode = 'admin'"
            >
              {{ auth.isAdmin ? '系统管理' : '个人中心' }}
            </button>
          </div>
        </div>

        <!-- 模式 A：一级分类 + 二级数据板块树形菜单 -->
        <nav v-if="sbMode === 'modules' || !expanded" class="sb-list" aria-label="数据板块树形导航">
          <RouterLink
            to="/dashboard"
            class="sb-item"
            :class="{ active: route.path === '/dashboard' }"
            v-tip:right="navTip('控制台概览')"
          >
            <LayoutGrid class="sb-ico" />
            <span class="sb-label">控制台概览</span>
          </RouterLink>

          <div class="sb-divider"></div>

          <!-- 1级 = 分类，2级 = 分类下所属的板块 -->
          <div
            v-for="grp in moduleGroups"
            :key="grp.key"
            class="sb-tree-group"
            :class="{ 'is-open': !collapsedCats[grp.key], 'has-active': isGroupActive(grp) }"
          >
            <!-- 一级菜单：分类 -->
            <button
              v-if="expanded"
              type="button"
              class="sb-item sb-cat-row"
              :aria-expanded="!collapsedCats[grp.key]"
              @click="toggleCat(grp.key)"
            >
              <AppIcon :name="grp.icon" fallback="Folder" class="sb-ico sb-cat-ico" />
              <span class="sb-label">{{ grp.name }}</span>
              <span class="sb-cat-count">{{ grp.modules.length }}</span>
              <ChevronRight class="sb-tree-chevron" />
            </button>

            <!-- 二级菜单：该分类下的板块 -->
            <div v-show="!collapsedCats[grp.key] || !expanded" class="sb-sub-list">
              <RouterLink
                v-for="m in grp.modules"
                :key="m.id"
                :to="`/m/${m.id}`"
                class="sb-item sb-sub-item"
                :class="{ active: route.path === `/m/${m.id}` }"
                v-tip:right="navTip(`${grp.name} / ${m.name}`)"
              >
                <AppIcon :name="m.icon" fallback="Database" class="sb-ico" />
                <span class="sb-label">{{ m.name }}</span>
                <span v-if="m.record_count && expanded" class="sb-sub-count">{{ formatCount(m.record_count) }}</span>
              </RouterLink>
            </div>
          </div>

          <template v-if="!moduleGroups.length && expanded">
            <RouterLink v-if="auth.isAdmin" to="/admin/modules" class="sb-empty">
              <Plus />新建第一个数据板块
            </RouterLink>
            <div v-else class="sb-empty is-static">暂无可访问的板块</div>
          </template>
        </nav>

        <!-- 模式 B：系统管理完整列表 -->
        <nav v-else class="sb-list" aria-label="系统管理导航">
          <template v-if="auth.isAdmin">
            <div class="sb-group-title">结构建模</div>
            <RouterLink
              to="/admin/categories"
              class="sb-item"
              :class="{ active: route.path === '/admin/categories' }"
            >
              <Folder class="sb-ico" />
              <span class="sb-label">分类管理</span>
              <ChevronRight class="sb-item-chevron" />
            </RouterLink>
            <RouterLink
              to="/admin/fields"
              class="sb-item"
              :class="{ active: route.path === '/admin/fields' }"
            >
              <List class="sb-ico" />
              <span class="sb-label">字段管理</span>
              <ChevronRight class="sb-item-chevron" />
            </RouterLink>
            <RouterLink
              to="/admin/modules"
              class="sb-item"
              :class="{ active: route.path === '/admin/modules' }"
            >
              <Layers class="sb-ico" />
              <span class="sb-label">板块管理</span>
              <ChevronRight class="sb-item-chevron" />
            </RouterLink>

            <div class="sb-group-title mt-2">系统运维</div>
            <RouterLink
              to="/admin/users"
              class="sb-item"
              :class="{ active: route.path === '/admin/users' }"
            >
              <Users class="sb-ico" />
              <span class="sb-label">用户与权限</span>
              <ChevronRight class="sb-item-chevron" />
            </RouterLink>
            <RouterLink
              to="/admin/backups"
              class="sb-item"
              :class="{ active: route.path === '/admin/backups' }"
            >
              <Archive class="sb-ico" />
              <span class="sb-label">数据备份</span>
              <ChevronRight class="sb-item-chevron" />
            </RouterLink>
            <RouterLink
              to="/admin/audit"
              class="sb-item"
              :class="{ active: route.path === '/admin/audit' }"
            >
              <History class="sb-ico" />
              <span class="sb-label">操作日志</span>
              <ChevronRight class="sb-item-chevron" />
            </RouterLink>
          </template>
          <RouterLink
            to="/admin/account"
            class="sb-item"
            :class="{ active: route.path === '/admin/account' }"
          >
            <ShieldCheck class="sb-ico" />
            <span class="sb-label">账号安全</span>
            <ChevronRight class="sb-item-chevron" />
          </RouterLink>
        </nav>

        <!-- 最底部蓝色 Collapse 折叠条 -->
        <div v-if="!isMobile" class="sb-collapse-foot">
          <button
            type="button"
            class="sb-collapse-btn"
            :aria-label="expanded ? '收起侧栏' : '展开侧栏'"
            v-tip:right="expanded ? '' : '展开侧栏'"
            @click="collapsed = !collapsed"
          >
            <ChevronsLeft v-if="expanded" />
            <ChevronsRight v-else />
            <span v-if="expanded">收起</span>
          </button>
        </div>
        <div v-else class="sb-collapse-foot">
          <button type="button" class="sb-collapse-btn" @click="mobileOpen = false">
            <X />
            <span>关闭菜单</span>
          </button>
        </div>
      </aside>

      <!-- 右侧纯白主内容画布 -->
      <main class="ovh-main">
        <router-view />
      </main>
    </div>

    <div v-if="mobileOpen" class="sidebar-backdrop" @click="mobileOpen = false"></div>

    <CommandPalette v-model="paletteOpen" />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  Archive,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Folder,
  History,
  Layers,
  LayoutGrid,
  List,
  LogOut,
  Menu,
  Moon,
  Plus,
  Search,
  ShieldCheck,
  Sun,
  Users,
  X,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useNavStore } from '@/stores/nav'
import { useThemeStore } from '@/stores/theme'
import { findSystemNav } from '@/config/nav'
import AppIcon from '@/components/AppIcon.vue'
import CommandPalette from '@/components/CommandPalette.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const nav = useNavStore()
const theme = useThemeStore()

const paletteOpen = ref(false)
const userMenuOpen = ref(false)
const userMenuEl = ref<HTMLElement>()
const sbMode = ref<'modules' | 'admin'>(route.path.startsWith('/admin') ? 'admin' : 'modules')

function readCollapsedCats(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem('ui.collapsedCats') || '{}') || {}
  } catch {
    return {}
  }
}
const collapsedCats = reactive<Record<string, boolean>>(readCollapsedCats())
function toggleCat(key: string) {
  collapsedCats[key] = !collapsedCats[key]
  localStorage.setItem('ui.collapsedCats', JSON.stringify(collapsedCats))
}

const roleLabel = computed(() => (auth.isAdmin ? '系统管理员' : '普通成员'))

/* ---------- 折叠 / 响应式 ---------- */
const collapsed = ref(localStorage.getItem('ui.sidebarCollapsed') === '1')
watch(collapsed, (v) => localStorage.setItem('ui.sidebarCollapsed', v ? '1' : '0'))

const mql = window.matchMedia('(max-width: 991.98px)')
const isMobile = ref(mql.matches)
const mobileOpen = ref(false)

const isCollapsed = computed(() => collapsed.value && !isMobile.value)
const expanded = computed(() => !isCollapsed.value)

function onMqlChange(e: MediaQueryListEvent) {
  isMobile.value = e.matches
  if (!e.matches) mobileOpen.value = false
}

function onWinKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (mobileOpen.value) mobileOpen.value = false
    if (userMenuOpen.value) userMenuOpen.value = false
  }
}

function onDocClick(e: MouseEvent) {
  if (userMenuOpen.value && userMenuEl.value && !userMenuEl.value.contains(e.target as Node)) {
    userMenuOpen.value = false
  }
}

watch(
  () => route.path,
  (p) => {
    mobileOpen.value = false
    userMenuOpen.value = false
    if (p.startsWith('/admin')) {
      sbMode.value = 'admin'
    } else if (p.startsWith('/m/')) {
      sbMode.value = 'modules'
      const mod = nav.modules.find((m) => `/m/${m.id}` === p)
      if (mod) {
        const key = mod.category_id ? `c${mod.category_id}` : 'none'
        if (collapsedCats[key]) {
          collapsedCats[key] = false
          localStorage.setItem('ui.collapsedCats', JSON.stringify(collapsedCats))
        }
      }
    }
    window.scrollTo({ top: 0 })
  }
)

watch(mobileOpen, (v) => document.body.classList.toggle('no-scroll', v))

onMounted(() => {
  mql.addEventListener('change', onMqlChange)
  window.addEventListener('keydown', onWinKeydown)
  document.addEventListener('mousedown', onDocClick)
  nav.refresh()
})

onBeforeUnmount(() => {
  mql.removeEventListener('change', onMqlChange)
  window.removeEventListener('keydown', onWinKeydown)
  document.removeEventListener('mousedown', onDocClick)
  document.body.classList.remove('no-scroll')
})

function navTip(label: string): string {
  return isCollapsed.value ? label : ''
}

/* ---------- 一级分类 + 二级板块树形分组 ---------- */
const moduleGroups = computed(() => {
  const groups = nav.categories
    .map((c) => ({
      key: `c${c.id}`,
      name: c.name,
      icon: c.icon as string | null | undefined,
      modules: nav.modules.filter((m) => m.category_id === c.id),
    }))
    .filter((g) => g.modules.length > 0)
  const uncategorized = nav.modules.filter((m) => !m.category_id)
  if (uncategorized.length > 0) {
    groups.push({ key: 'none', name: '未分类', icon: 'Folder', modules: uncategorized })
  }
  return groups
})

function isGroupActive(grp: { modules: { id: number }[] }): boolean {
  return grp.modules.some((m) => route.path === `/m/${m.id}`)
}

function formatCount(n: number) {
  return n >= 10000 ? `${Math.floor(n / 1000) / 10}w` : String(n)
}

const currentModule = computed(() =>
  route.params.moduleId ? nav.modules.find((m) => String(m.id) === String(route.params.moduleId)) : undefined
)

/* ---------- 页面标题 ---------- */
const currentTitle = computed(() => {
  if (route.path === '/dashboard') return '控制台概览'
  if (route.params.moduleId) return currentModule.value?.name || (route.meta.title as string) || '数据记录'
  return findSystemNav(route.path)?.label || (route.meta.title as string) || 'Message_Info'
})

watch(
  currentTitle,
  (t) => {
    document.title = `${t} · Message_Info Console`
  },
  { immediate: true }
)

const userInitials = computed(() => {
  const name = (auth.username || 'AD').trim()
  return name.slice(0, 2).toUpperCase()
})

function onLogout() {
  userMenuOpen.value = false
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
/* ==========================================================================
   OVHcloud Console App Shell（顶白通栏 + 左白双胶囊功能栏 + 纯白无界主画布）
   ========================================================================== */

.ovh-shell {
  display: flex;
  min-height: 100vh;
  flex-direction: column;
  background: var(--bg);
}

/* ---------- 顶部纯白通栏导航 ---------- */
.ovh-topbar {
  position: sticky;
  top: 0;
  z-index: 1030;
  display: flex;
  height: var(--topbar-h);
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 0 24px;
  border-bottom: 1px solid var(--surface-border);
  background: var(--bg-topbar);
}

.ovh-topbar-left {
  display: flex;
  height: 100%;
  min-width: 0;
  align-items: center;
  gap: 18px;
}

.ovh-brand {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  color: var(--ovh-navy);
  text-decoration: none;
  flex-shrink: 0;
}

.ovh-brand-mark {
  display: inline-flex;
  width: 34px;
  height: 28px;
  align-items: center;
  justify-content: center;
}

.ovh-brand-mark svg {
  width: 34px;
  height: 28px;
}

.ovh-brand-name {
  color: var(--ovh-navy);
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.ovh-console-pill {
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: var(--ovh-navy);
  color: #ffffff;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

html[data-theme='dark'] .ovh-console-pill {
  background: var(--ovh-blue);
}

/* 顶栏右侧工具与用户圆章 */
.ovh-topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.top-icon-btn {
  display: inline-grid;
  width: 34px;
  height: 34px;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--text-soft);
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease;
}

.top-icon-btn:hover {
  background: var(--ovh-ice);
  color: var(--ovh-blue);
}

.top-icon-btn .lucide {
  width: 17px;
  height: 17px;
}

.ovh-user-wrap {
  position: relative;
  margin-left: 4px;
}

.ovh-avatar-btn {
  display: inline-grid;
  width: 34px;
  height: 34px;
  place-items: center;
  padding: 0;
  border: 1px solid var(--surface-border);
  border-radius: 50%;
  background: var(--bg-subtle);
  color: var(--ovh-navy-ink);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: border-color 0.14s ease, background 0.14s ease;
}

.ovh-avatar-btn:hover {
  border-color: var(--ovh-ice-border);
  background: var(--ovh-ice);
  color: var(--ovh-navy);
}

.ovh-user-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 1060;
  width: 220px;
  padding: 6px;
  border: 1px solid var(--surface-border);
  border-radius: 10px;
  background: var(--bg-elev-strong);
  box-shadow: var(--shadow-lg);
}

.ovh-user-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
}

.ovh-avatar-sm {
  display: grid;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 50%;
  background: var(--ovh-ice);
  color: var(--ovh-navy);
  font-size: 12px;
  font-weight: 700;
}

.ovh-user-name {
  color: var(--ovh-navy-ink);
  font-size: 14px;
  font-weight: 600;
}

.ovh-user-role {
  color: var(--text-muted);
  font-size: 12px;
}

.ovh-menu-sep {
  height: 1px;
  margin: 5px 0;
  background: var(--hairline);
}

.ovh-menu-item {
  display: flex;
  width: 100%;
  height: 34px;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text-soft);
  font-size: 13px;
  text-decoration: none;
  cursor: pointer;
}

.ovh-menu-item .lucide {
  width: 15px;
  height: 15px;
  color: var(--text-muted);
}

.ovh-menu-item:hover {
  background: var(--ovh-ice);
  color: var(--ovh-navy);
}

.ovh-menu-item.is-danger {
  color: var(--danger);
}

.ovh-menu-item.is-danger .lucide {
  color: var(--danger);
}

.ovh-menu-item.is-danger:hover {
  background: var(--danger-soft);
}

.pop-enter-active,
.pop-leave-active {
  transition: opacity 0.12s ease, transform 0.12s ease;
}

.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ---------- 下方主体 ---------- */
.ovh-body {
  display: grid;
  flex: 1 1 auto;
  grid-template-columns: var(--sidebar-w) minmax(0, 1fr);
  transition: grid-template-columns 0.18s ease;
}

.ovh-shell.is-collapsed .ovh-body {
  grid-template-columns: var(--sidebar-w-collapsed) minmax(0, 1fr);
}

/* ---------- 左侧纯白导航栏 ---------- */
.ovh-sidebar {
  position: sticky;
  top: var(--topbar-h);
  z-index: 1020;
  display: flex;
  height: calc(100vh - var(--topbar-h));
  flex-direction: column;
  border-right: 1px solid var(--surface-border);
  background: var(--bg-sidebar);
  user-select: none;
}

/* OVH 左上双胶囊切换器 (Products | My services) */
.sb-top-ctrl {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 10px 8px;
}

.ovh-dual-pills {
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 2px;
  border: 1px solid var(--surface-border);
  border-radius: 999px;
  background: var(--bg-soft);
  gap: 2px;
}

.ovh-dual-pill {
  height: 28px;
  padding: 0 9px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--text-soft);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease, box-shadow 0.14s ease;
}

.ovh-dual-pill:hover {
  color: var(--ovh-navy);
}

.ovh-dual-pill.active {
  background: var(--bg-elev);
  color: var(--ovh-navy);
  font-weight: 600;
  box-shadow: var(--shadow-xs);
}

/* 一级分类 + 二级板块树形菜单 */
.sb-tree-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 2px;
}

.sb-cat-row {
  width: 100%;
  border: 0;
  background: transparent;
  color: var(--ovh-navy-ink);
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.sb-tree-group.has-active > .sb-cat-row {
  color: var(--ovh-navy);
}

.sb-tree-group.has-active > .sb-cat-row .sb-cat-ico {
  color: var(--ovh-blue);
}

.sb-cat-count {
  padding: 0 5px;
  border-radius: 999px;
  background: var(--bg-subtle);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  line-height: 16px;
}

.sb-tree-chevron {
  width: 13px;
  height: 13px;
  color: var(--text-faint);
  transition: transform 0.15s ease;
}

.sb-tree-group.is-open .sb-tree-chevron {
  transform: rotate(90deg);
}

.sb-sub-list {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1px;
  margin: 1px 0 3px 16px;
  padding-left: 8px;
  border-left: 1px solid var(--surface-border);
}

.is-collapsed .sb-sub-list {
  margin: 0;
  padding-left: 0;
  border-left: 0;
}

.sb-sub-item {
  height: 31px;
  padding: 0 9px;
}

.sb-sub-count {
  color: var(--text-faint);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.sb-sub-item.active .sb-sub-count {
  color: var(--ovh-blue);
  font-weight: 600;
}

/* 板块滚动区 */
.sb-list {
  flex: 1 1 auto;
  overflow-y: auto;
  padding: 6px 10px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sb-group-title {
  padding: 8px 10px 4px;
  color: var(--text-faint);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.sb-divider {
  height: 1px;
  margin: 8px 6px;
  background: var(--hairline);
}

.sb-item {
  display: flex;
  height: 34px;
  align-items: center;
  gap: 9px;
  padding: 0 11px;
  border-radius: 6px;
  color: var(--text-soft);
  font-size: 13px;
  font-weight: 400;
  text-decoration: none;
  transition: background 0.12s ease, color 0.12s ease;
}

.is-collapsed .sb-item {
  justify-content: center;
  padding: 0;
}

.is-collapsed .sb-label {
  display: none;
}

.sb-item:hover {
  background: var(--bg-hover);
  color: var(--ovh-navy);
}

.sb-item.active {
  background: var(--ovh-ice);
  color: var(--ovh-navy);
  font-weight: 600;
}

.sb-ico {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
  color: var(--text-muted);
}

.sb-item:hover .sb-ico,
.sb-item.active .sb-ico {
  color: var(--ovh-blue);
}

.sb-label {
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sb-item-chevron {
  width: 13px;
  height: 13px;
  color: var(--text-faint);
}

.sb-empty {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 6px 2px;
  padding: 10px 12px;
  border: 1px dashed var(--surface-border);
  border-radius: 6px;
  color: var(--ovh-blue);
  font-size: 13px;
  text-decoration: none;
}

.sb-empty.is-static {
  color: var(--text-muted);
}

/* 最底部蓝色 Collapse 栏 */
.sb-collapse-foot {
  padding: 8px 12px;
  border-top: 1px solid var(--hairline);
}

.sb-collapse-btn {
  display: inline-flex;
  height: 30px;
  align-items: center;
  gap: 6px;
  padding: 0 8px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--ovh-blue);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.is-collapsed .sb-collapse-foot {
  display: flex;
  justify-content: center;
  padding: 8px 6px;
}

.sb-collapse-btn:hover {
  background: var(--ovh-ice);
}

.sb-collapse-btn .lucide {
  width: 15px;
  height: 15px;
}

/* 主内容区 */
.ovh-main {
  min-width: 0;
  background: var(--bg);
}

.sidebar-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1015;
  background: var(--bg-overlay);
}

@media (max-width: 991.98px) {
  .ovh-body,
  .ovh-shell.is-collapsed .ovh-body {
    grid-template-columns: minmax(0, 1fr);
  }

  .ovh-sidebar {
    position: fixed;
    top: var(--topbar-h);
    bottom: 0;
    left: 0;
    width: 268px;
    height: calc(100vh - var(--topbar-h));
    transform: translateX(-100%);
    transition: transform 0.2s ease;
  }

  .ovh-shell.is-mobile-open .ovh-sidebar {
    transform: translateX(0);
    box-shadow: var(--shadow-xl);
  }
}
</style>
