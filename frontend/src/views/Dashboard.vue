<template>
  <div class="page">
    <!-- OVH 晴空渐变页头横幅（右侧纯留白渐变，按钮统一下移至工具栏左起） -->
    <PageHeader title="控制台概览" eyebrow="控制台">
      <template v-if="isAdmin" #links>
        <RouterLink to="/admin/audit"><History />操作日志</RouterLink>
        <RouterLink to="/admin/backups"><Archive />数据备份</RouterLink>
      </template>
      <template #subtitle>
        <span class="dash-status">
          <template v-if="isAdmin">
            <span class="status-dot on"></span>
            <span>SQLite WAL 运行正常</span>
            <span class="dash-sep">·</span>
            <span>Fernet 加密守护</span>
            <span class="dash-sep">·</span>
            <RouterLink to="/admin/backups" class="dash-status-link">
              最近快照：{{ lastBackup || '尚未备份' }}
            </RouterLink>
            <template v-if="schedule.enabled">
              <span class="dash-sep">·</span>
              <span>每 {{ schedule.interval_hours }} 小时自动备份</span>
            </template>
          </template>
          <template v-else>
            <span>欢迎回来，{{ auth.username }} · 点击下方任意业务板块进入数据管理</span>
          </template>
        </span>
      </template>
    </PageHeader>

    <!-- OVH 标准顶行操作栏（左：钴蓝主按钮 + 次按钮；右：搜索 + 视图切换） -->
    <div class="ovh-toolbar">
      <div class="toolbar-group">
        <template v-if="isAdmin">
          <button class="btn btn-primary" @click="$router.push('/admin/modules')">
            <Plus />新建数据板块
          </button>
          <button class="btn btn-outline-secondary" :disabled="backingUp" @click="onBackup">
            <span v-if="backingUp" class="spinner-border spinner-border-sm"></span>
            <Archive v-else />立即生成快照
          </button>
        </template>
        <div v-if="categoryPills.length > 1" class="cat-pills">
          <button
            v-for="cat in categoryPills"
            :key="cat.key"
            type="button"
            class="cat-pill"
            :class="{ active: activeCategory === cat.key }"
            @click="activeCategory = cat.key"
          >
            {{ cat.label }}
          </button>
        </div>
      </div>

      <div class="toolbar-group">
        <div class="search-box d-none d-sm-flex" style="width: 240px">
          <Search />
          <input v-model="filter" class="form-control" placeholder="搜索板块名称或编码…" />
          <button v-if="filter" class="search-box-clear" type="button" aria-label="清除" @click="filter = ''">
            <X />
          </button>
        </div>
        <div class="segmented icon-only">
          <button
            type="button"
            class="segmented-btn"
            :class="{ active: viewMode === 'grid' }"
            v-tip="'产品目录卡片'"
            @click="viewMode = 'grid'"
          >
            <LayoutGrid />
          </button>
          <button
            type="button"
            class="segmented-btn"
            :class="{ active: viewMode === 'table' }"
            v-tip="'控制台列表'"
            @click="viewMode = 'table'"
          >
            <Table />
          </button>
        </div>
      </div>
    </div>

    <!-- 一体式指标带 -->
    <div class="metric-strip">
      <template v-if="loading && firstLoad">
        <div v-for="i in 4" :key="i" class="metric">
          <Skeleton variant="line" width="38%" />
          <Skeleton variant="rect" height="30px" width="48%" class="mt-2" />
          <Skeleton variant="line" width="56%" class="mt-2" />
        </div>
      </template>
      <template v-else>
        <component
          :is="kpi.to ? RouterLink : 'div'"
          v-for="kpi in kpis"
          :key="kpi.label"
          :to="kpi.to"
          class="metric"
        >
          <span class="metric-top">
            <span>{{ kpi.label }}</span>
            <ArrowUpRight v-if="kpi.to" class="metric-arrow" />
          </span>
          <span class="metric-value">{{ kpi.value }}</span>
          <span class="metric-sub">{{ kpi.sub }}</span>
        </component>
      </template>
    </div>

    <!-- 首次引导（配置完成后自动隐藏） -->
    <section v-if="isAdmin && !firstLoad && !setupDone" class="setup-box">
      <div class="setup-head">
        <span class="setup-title">快速上手 · 已完成 {{ doneCount }} / 4</span>
        <span class="setup-bar"><span :style="{ width: `${(doneCount / 4) * 100}%` }"></span></span>
      </div>
      <div class="setup-grid">
        <RouterLink
          v-for="(s, i) in setupSteps"
          :key="s.title"
          :to="s.to"
          class="setup-step"
          :class="{ done: s.done }"
        >
          <span class="setup-num">
            <Check v-if="s.done" />
            <template v-else>{{ i + 1 }}</template>
          </span>
          <span class="setup-body">
            <span class="setup-step-title">{{ s.title }}</span>
            <span class="setup-step-desc">{{ s.desc }}</span>
          </span>
          <ArrowRight class="setup-arrow" />
        </RouterLink>
      </div>
    </section>

    <!-- 全宽数据板块区 -->
    <section class="dash-section">
      <SkeletonTable v-if="loading && firstLoad" :rows="5" :cols="5" />

      <!-- OVH 云产品目录卡片网格 -->
      <template v-else-if="viewMode === 'grid'">
        <div v-if="filteredModules.length" class="mod-grid">
          <RouterLink v-for="row in filteredModules" :key="row.id" :to="`/m/${row.id}`" class="mod-card">
            <div class="mod-top">
              <span class="mod-ico">
                <AppIcon :name="row.icon" fallback="Database" />
              </span>
              <div class="mod-head-meta">
                <span class="mod-cat">{{ moduleCategoryName(row.category_id) }}</span>
                <code class="code-sm">{{ row.code }}</code>
              </div>
              <span v-if="!row.is_enabled" class="badge text-bg-secondary ms-auto">已禁用</span>
              <span v-else class="badge badge-dot text-bg-success ms-auto">运行中</span>
            </div>
            <div class="mod-name" :title="row.name">{{ row.name }}</div>
            <div v-if="row.description" class="mod-desc" :title="row.description">
              {{ row.description }}
            </div>
            <div class="mod-foot">
              <span class="mod-meta">
                <strong>{{ formatNumber(row.record_count) }}</strong> 条记录
                <span class="dash-sep">·</span>
                {{ row.field_count }} 个字段
              </span>
              <span class="mod-cta">浏览记录 <ArrowRight class="mod-arrow" /></span>
            </div>
          </RouterLink>
        </div>
        <div v-else class="panel">
          <div class="empty-state">
            <LayoutGrid />
            <div class="empty-state-title">
              {{ nav.modules.length ? '没有匹配的板块' : isAdmin ? '还没有数据板块' : '暂无可访问的板块' }}
            </div>
            <p>
              {{
                nav.modules.length
                  ? '请尝试更换筛选条件或关键词。'
                  : isAdmin
                    ? '创建第一个数据板块，即可开始录入和管理记录。'
                    : '管理员为您分配访问权限后会显示在这里。'
              }}
            </p>
            <button v-if="isAdmin && !nav.modules.length" class="btn btn-primary btn-sm" @click="$router.push('/admin/modules')">
              <Plus />新建板块
            </button>
          </div>
        </div>
      </template>

      <!-- OVH 无外框列表视图 -->
      <div v-else class="ovh-table-wrap">
        <div class="table-responsive">
          <table class="table table-hover align-middle">
            <thead>
              <tr>
                <th>板块</th>
                <th style="width: 140px">分类</th>
                <th class="text-end" style="width: 90px">字段</th>
                <th class="text-end" style="width: 100px">记录</th>
                <th style="width: 96px">状态</th>
                <th style="width: 120px" class="text-end">创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in filteredModules" :key="row.id" class="is-clickable" @click="$router.push(`/m/${row.id}`)">
                <td>
                  <span class="name-cell">
                    <span class="name-ico"><AppIcon :name="row.icon" fallback="Database" /></span>
                    <span class="name-text">
                      <span class="name-title">{{ row.name }}</span>
                      <span class="name-sub">{{ row.code }}</span>
                    </span>
                  </span>
                </td>
                <td><span class="badge badge-purple">{{ moduleCategoryName(row.category_id) }}</span></td>
                <td class="text-end cell-mono cell-muted">{{ row.field_count }}</td>
                <td class="text-end cell-mono fw-semibold">{{ formatNumber(row.record_count) }}</td>
                <td>
                  <span class="badge badge-dot" :class="row.is_enabled ? 'text-bg-success' : 'text-bg-secondary'">
                    {{ row.is_enabled ? '运行中' : '已禁用' }}
                  </span>
                </td>
                <td class="text-end cell-muted cell-mono">{{ formatRelative(row.created_at) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="!filteredModules.length" class="empty-state">
            <LayoutGrid />
            <div class="empty-state-title">{{ nav.modules.length ? '没有匹配的板块' : '暂无板块' }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 底部轻量动态流水（仅管理员） -->
    <section v-if="isAdmin && (recent.length || (loading && firstLoad))" class="dash-section">
      <div class="section-bar">
        <h2 class="section-title">最近操作审计</h2>
        <RouterLink to="/admin/audit" class="more-link">查看全部日志<ArrowRight /></RouterLink>
      </div>
      <div class="panel">
        <div v-if="loading && firstLoad" class="panel-body d-flex flex-column gap-3">
          <Skeleton v-for="i in 4" :key="i" variant="line" :width="`${55 + ((i * 23) % 35)}%`" />
        </div>
        <ul v-else class="feed-list">
          <li v-for="a in recent" :key="a.id" class="feed-item">
            <span class="status-dot" :class="dotTone(a.action)"></span>
            <span class="feed-action">{{ a.action }}</span>
            <span class="feed-summary" :title="a.summary">
              {{ a.summary || `${a.entity_type || ''} #${a.entity_id ?? ''}` }}
            </span>
            <span class="feed-time">{{ formatRelative(a.created_at) }}</span>
          </li>
        </ul>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import {
  Archive,
  ArrowRight,
  ArrowUpRight,
  Check,
  History,
  LayoutGrid,
  Plus,
  Search,
  Table,
  X,
} from 'lucide-vue-next'
import { systemApi } from '@/api'
import { useNavStore } from '@/stores/nav'
import { useAuthStore } from '@/stores/auth'
import { toast } from '@/utils/ui'
import PageHeader from '@/components/ui/PageHeader.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import SkeletonTable from '@/components/ui/SkeletonTable.vue'
import AppIcon from '@/components/AppIcon.vue'

const info = reactive({ module_total: 0, field_total: 0, record_total: 0, user_total: 0, owned_total: 0 })
const schedule = reactive({ enabled: false, interval_hours: 24, last_run_at: null as string | null })
const nav = useNavStore()
const auth = useAuthStore()
const isAdmin = computed(() => auth.isAdmin)
const backingUp = ref(false)
const loading = ref(false)
const firstLoad = ref(true)
const recent = ref<any[]>([])
const lastBackup = ref('')
const filter = ref('')
const activeCategory = ref('all')

const viewMode = ref<'grid' | 'table'>((localStorage.getItem('ui.dashboardViewMode') as 'grid' | 'table') || 'grid')
watch(viewMode, (v) => localStorage.setItem('ui.dashboardViewMode', v))

const categoryPills = computed(() => {
  const pills: { key: string; label: string }[] = [{ key: 'all', label: '全部' }]
  for (const c of nav.categories) {
    if (nav.modules.some((m) => m.category_id === c.id)) {
      pills.push({ key: String(c.id), label: c.name })
    }
  }
  if (nav.modules.some((m) => !m.category_id)) {
    pills.push({ key: 'none', label: '未分类' })
  }
  return pills
})

const filteredModules = computed(() => {
  let list = nav.modules
  if (activeCategory.value === 'none') {
    list = list.filter((m) => !m.category_id)
  } else if (activeCategory.value !== 'all') {
    list = list.filter((m) => String(m.category_id) === activeCategory.value)
  }
  const k = filter.value.trim().toLowerCase()
  if (!k) return list
  return list.filter(
    (m) =>
      m.name.toLowerCase().includes(k) ||
      m.code.toLowerCase().includes(k) ||
      moduleCategoryName(m.category_id).toLowerCase().includes(k)
  )
})

const memberKpis = computed(() => [
  { label: '可访问板块', value: formatNumber(info.module_total), sub: '当前权限可见业务表', to: '' },
  { label: '可见记录', value: formatNumber(info.record_total), sub: '全部可查阅数据', to: '' },
  { label: '我创建的', value: formatNumber(info.owned_total), sub: '拥有完整编辑权限', to: '' },
  { label: '共享给我', value: formatNumber(Math.max(0, info.record_total - info.owned_total)), sub: '团队分配记录', to: '' },
])

const adminKpis = computed(() => [
  { label: '数据板块', value: formatNumber(info.module_total), sub: `归属 ${nav.categories.length} 个分类`, to: '/admin/modules' },
  { label: '字段库', value: formatNumber(info.field_total), sub: '跨板块可复用字段', to: '/admin/fields' },
  { label: '记录总量', value: formatNumber(info.record_total), sub: '全库结构化数据', to: '' },
  { label: '系统成员', value: formatNumber(info.user_total), sub: '账号与权限管理', to: '/admin/users' },
])

const kpis = computed(() => (isAdmin.value ? adminKpis.value : memberKpis.value))

const setupSteps = computed(() => [
  { title: '创建分类', desc: '规划板块分组', to: '/admin/categories', done: nav.categories.length > 0 },
  { title: '定义字段', desc: '建立可复用字段', to: '/admin/fields', done: info.field_total > 0 },
  { title: '创建板块', desc: '组合字段建表', to: '/admin/modules', done: info.module_total > 0 },
  {
    title: '录入数据',
    desc: '新增第一条记录',
    to: nav.modules[0] ? `/m/${nav.modules[0].id}` : '/admin/modules',
    done: info.record_total > 0,
  },
])
const doneCount = computed(() => setupSteps.value.filter((s) => s.done).length)
const setupDone = computed(() => doneCount.value === setupSteps.value.length)

onMounted(async () => {
  loading.value = true
  try {
    const admin = isAdmin.value
    const tasks: Promise<any>[] = [
      systemApi.info(),
      nav.refresh(),
      admin ? systemApi.audit({ page: 1, page_size: 6 }).catch(() => null) : Promise.resolve(null),
      admin ? systemApi.backupSchedule().catch(() => null) : Promise.resolve(null),
      admin ? systemApi.backups().catch(() => null) : Promise.resolve(null),
    ]
    const [infoRes, , auditRes, scheduleRes, backupsRes] = await Promise.all(tasks)
    Object.assign(info, infoRes.data)
    if (auditRes) recent.value = auditRes.data.items || []
    if (scheduleRes) Object.assign(schedule, scheduleRes.data)
    if (backupsRes && backupsRes.data.items?.length) {
      lastBackup.value = formatRelative(backupsRes.data.items[0].created_at)
    }
  } finally {
    loading.value = false
    firstLoad.value = false
  }
})

function moduleCategoryName(categoryId?: number | null) {
  if (!categoryId) return '未分类'
  return nav.categories.find((c) => c.id === categoryId)?.name || '未分类'
}

async function onBackup() {
  backingUp.value = true
  try {
    const { data } = await systemApi.backup()
    toast(`备份完成：${data.filename}`, 'success')
    const { data: list } = await systemApi.backups()
    if (list.items?.length) lastBackup.value = formatRelative(list.items[0].created_at)
  } finally {
    backingUp.value = false
  }
}

function formatNumber(value: number) {
  return Number(value || 0).toLocaleString('zh-CN')
}

function formatRelative(s: string) {
  if (!s) return ''
  const d = new Date(s)
  const diff = Date.now() - d.getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return '刚才'
  if (min < 60) return `${min}分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}小时前`
  const day = Math.floor(hr / 24)
  if (day < 30) return `${day}天前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function dotTone(action: string) {
  if (!action) return 'off'
  const a = action.toLowerCase()
  if (a.includes('create') || a.includes('add') || a.includes('新增') || a.includes('创建')) return 'on'
  if (a.includes('delete') || a.includes('remove') || a.includes('purge') || a.includes('删除')) return 'err'
  if (a.includes('update') || a.includes('edit') || a.includes('修改') || a.includes('保存')) return 'warn'
  return 'off'
}
</script>

<style scoped>
.dash-status {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 7px;
  font-size: 13px;
}

.dash-sep {
  color: var(--text-faint);
}

.dash-status-link {
  color: var(--ovh-blue);
  font-weight: 500;
}

.dash-status-link:hover {
  text-decoration: underline;
}

/* ---------- 首次引导 ---------- */
.setup-box {
  margin-bottom: 24px;
  padding: 16px 20px;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-card);
  background: var(--bg-elev);
}

.setup-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.setup-title {
  color: var(--ovh-navy-ink);
  font-size: 14px;
  font-weight: 600;
}

.setup-bar {
  width: 140px;
  height: 5px;
  border-radius: 999px;
  background: var(--bg-subtle);
  overflow: hidden;
}

.setup-bar span {
  display: block;
  height: 100%;
  background: var(--ovh-blue);
  transition: width 0.25s ease;
}

.setup-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

@media (max-width: 991.98px) {
  .setup-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 575.98px) {
  .setup-grid {
    grid-template-columns: 1fr;
  }
}

.setup-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 13px;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius);
  background: var(--bg-soft);
  color: var(--text);
  text-decoration: none;
  transition: border-color 0.14s ease, background 0.14s ease;
}

.setup-step:hover {
  border-color: var(--ovh-ice-border);
  background: var(--ovh-ice);
}

.setup-num {
  display: grid;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  place-items: center;
  border: 1px solid var(--surface-border);
  border-radius: 50%;
  background: var(--bg-elev);
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
}

.setup-step.done .setup-num {
  border-color: transparent;
  background: var(--ovh-blue);
  color: #ffffff;
}

.setup-num .lucide {
  width: 13px;
  height: 13px;
}

.setup-body {
  display: flex;
  min-width: 0;
  flex: 1 1 auto;
  flex-direction: column;
}

.setup-step-title {
  color: var(--ovh-navy-ink);
  font-size: 13px;
  font-weight: 600;
}

.setup-step.done .setup-step-title {
  color: var(--text-muted);
  text-decoration: line-through;
}

.setup-step-desc {
  color: var(--text-muted);
  font-size: 12px;
}

.setup-arrow {
  width: 14px;
  height: 14px;
  color: var(--ovh-blue);
}

/* ---------- 板块区 ---------- */
.dash-section {
  margin-bottom: 28px;
}

.dash-section:last-child {
  margin-bottom: 0;
}

.section-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.section-title {
  margin: 0;
  color: var(--ovh-navy-ink);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.015em;
}

.cat-pills {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.cat-pill {
  height: 28px;
  padding: 0 12px;
  border: 1px solid var(--surface-border);
  border-radius: 999px;
  background: var(--bg-elev);
  color: var(--text-soft);
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease, border-color 0.14s ease;
}

.cat-pill:hover {
  border-color: var(--ovh-ice-border);
  background: var(--bg-hover);
  color: var(--ovh-navy);
}

.cat-pill.active {
  border-color: var(--ovh-blue);
  background: var(--ovh-ice);
  color: var(--ovh-navy);
  font-weight: 600;
}

/* ---------- OVH 产品目录卡片网格 ---------- */
.mod-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

@media (max-width: 1199.98px) {
  .mod-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767.98px) {
  .mod-grid {
    grid-template-columns: 1fr;
  }
}

.mod-card {
  display: flex;
  flex-direction: column;
  padding: 18px 20px 16px;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-card);
  background: var(--bg-elev);
  box-shadow: var(--shadow-card);
  color: var(--text);
  text-decoration: none;
  transition: border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease;
}

.mod-card:hover {
  border-color: var(--ovh-blue);
  box-shadow: var(--shadow-md);
  color: var(--text);
  transform: translateY(-2px);
}

.mod-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.mod-ico {
  display: grid;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  place-items: center;
  border: 1px solid var(--ovh-ice-border);
  border-radius: 8px;
  background: var(--ovh-ice);
  color: var(--ovh-blue);
}

.mod-ico .lucide {
  width: 17px;
  height: 17px;
}

.mod-head-meta {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
}

.mod-cat {
  color: var(--text-muted);
  font-size: 11.5px;
  font-weight: 500;
}

.mod-name {
  margin-bottom: 6px;
  overflow: hidden;
  color: var(--ovh-navy-ink);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.015em;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mod-card:hover .mod-name {
  color: var(--ovh-blue);
}

.mod-desc {
  display: -webkit-box;
  margin-bottom: 12px;
  overflow: hidden;
  color: var(--text-muted);
  font-size: 12.5px;
  line-height: 1.5;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.mod-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--hairline);
  font-size: 12.5px;
}

.mod-meta {
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.mod-meta strong {
  color: var(--ovh-navy-ink);
  font-weight: 700;
}

.mod-cta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--ovh-blue);
  font-weight: 600;
}

.mod-arrow {
  width: 13px;
  height: 13px;
  transition: transform 0.14s ease;
}

.mod-card:hover .mod-arrow {
  transform: translateX(3px);
}

/* ---------- 底部操作审计列表 ---------- */
.more-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--ovh-blue);
  font-size: 13px;
  font-weight: 500;
}

.more-link .lucide {
  width: 14px;
  height: 14px;
}

.feed-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.feed-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  border-bottom: 1px solid var(--hairline);
  font-size: 13px;
}

.feed-item:last-child {
  border-bottom: 0;
}

.feed-action {
  flex-shrink: 0;
  color: var(--ovh-navy-ink);
  font-weight: 600;
}

.feed-summary {
  flex: 1 1 auto;
  overflow: hidden;
  color: var(--text-muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.feed-time {
  flex-shrink: 0;
  color: var(--text-faint);
  font-family: var(--font-mono);
  font-size: 12px;
}
</style>
