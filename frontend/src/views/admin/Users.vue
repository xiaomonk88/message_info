<template>
  <div class="page">
    <PageHeader
      title="用户与权限"
      eyebrow="系统运维"
      subtitle="管理成员账号、自助注册开关及板块级访问授权（记录级共享在各板块记录列表中操作）"
    >
      <template #links>
        <RouterLink to="/admin/backups">数据备份</RouterLink>
        <RouterLink to="/admin/audit">操作日志</RouterLink>
        <RouterLink to="/admin/account">账号安全</RouterLink>
      </template>
    </PageHeader>

    <!-- OVH 单行操作栏：左起主按钮 + 自助注册开关；右起角色分段 + 搜索 -->
    <div class="ovh-toolbar">
      <div class="toolbar-group">
        <button class="btn btn-primary" @click="openCreate">
          <UserPlus />新建用户
        </button>

        <label class="reg-pill">
          <span class="reg-inline-text">自助注册</span>
          <span class="form-check form-switch mb-0">
            <input
              class="form-check-input"
              type="checkbox"
              role="switch"
              :checked="allowRegister"
              :disabled="savingReg"
              @change="toggleRegister(($event.target as HTMLInputElement).checked)"
            />
          </span>
        </label>

        <span class="toolbar-meta d-none d-lg-inline-flex ms-1">
          共 <strong>{{ list.length }}</strong> 人 · <strong>{{ adminCount }}</strong> 管理员 · <strong>{{ list.length - adminCount }}</strong> 成员
        </span>
      </div>

      <div class="toolbar-group">
        <div class="segmented">
          <button
            v-for="f in roleFilters"
            :key="f.id"
            type="button"
            class="segmented-btn"
            :class="{ active: roleFilter === f.id }"
            @click="roleFilter = f.id"
          >
            {{ f.label }}
          </button>
        </div>
        <div class="search-box">
          <Search />
          <input v-model="keyword" class="form-control" placeholder="搜索用户名 / 显示名称…" />
          <button v-if="keyword" class="search-box-clear" type="button" aria-label="清除" @click="keyword = ''">
            <X />
          </button>
        </div>
      </div>
    </div>

    <div class="ovh-table-wrap">
      <SkeletonTable v-if="loading && firstLoad" :rows="6" :cols="6" />
      <div v-else class="table-responsive" v-loading="loading && !firstLoad">
        <table class="table table-hover align-middle">
          <thead>
            <tr>
              <th>用户</th>
              <th style="width: 100px">角色</th>
              <th style="width: 90px">状态</th>
              <th style="width: 220px">访问范围</th>
              <th class="text-end" style="width: 100px">拥有记录</th>
              <th style="width: 120px">最近登录</th>
              <th style="width: 140px">注册时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in filtered" :key="u.id" :class="{ 'is-disabled': !u.is_active }" @dblclick="openEdit(u)">
              <td>
                <span class="name-cell">
                  <span class="user-avatar" :class="{ admin: u.role === 'admin' }">{{ initial(u) }}</span>
                  <span class="name-text">
                    <span class="name-title">
                      {{ u.display_name || u.username }}
                      <span v-if="u.id === auth.userId" class="badge text-bg-secondary ms-1">我</span>
                    </span>
                    <span class="name-sub">@{{ u.username }}</span>
                  </span>
                </span>
              </td>
              <td>
                <span class="badge" :class="u.role === 'admin' ? 'badge-purple' : 'text-bg-secondary'">
                  {{ u.role === 'admin' ? '管理员' : '成员' }}
                </span>
              </td>
              <td>
                <span class="badge badge-dot" :class="u.is_active ? 'text-bg-success' : 'text-bg-danger'">
                  {{ u.is_active ? '正常' : '已禁用' }}
                </span>
              </td>
              <td>
                <span v-if="u.role === 'admin'" class="cell-muted">全部板块与记录</span>
                <span v-else-if="!u.module_grants && !u.shared_records" class="cell-faint">尚未分配</span>
                <span v-else class="scope-text">
                  <span v-if="u.module_grants"><strong>{{ u.module_grants }}</strong> 个板块</span>
                  <span v-if="u.module_grants && u.shared_records" class="dot-sep">·</span>
                  <span v-if="u.shared_records"><strong>{{ u.shared_records }}</strong> 条分配记录</span>
                </span>
              </td>
              <td class="text-end cell-mono">{{ u.owned_records }}</td>
              <td class="cell-muted">{{ u.last_login_at ? formatRelative(u.last_login_at) : '从未登录' }}</td>
              <td class="cell-muted cell-last">
                <span>{{ formatDate(u.created_at) }}</span>
                <div class="row-float-actions" @dblclick.stop>
                  <button
                    class="icon-button sm primary"
                    :disabled="u.role === 'admin'"
                    v-tip="u.role === 'admin' ? '管理员拥有全部权限' : '分配板块权限'"
                    @click="openGrants(u)"
                  >
                    <KeyRound />
                  </button>
                  <button class="icon-button sm" v-tip="'编辑用户 (或双击行)'" @click="openEdit(u)"><SquarePen /></button>
                  <button
                    class="icon-button sm danger"
                    :disabled="u.id === auth.userId"
                    v-tip="u.id === auth.userId ? '不能删除自己' : '删除用户'"
                    @click="remove(u)"
                  >
                    <Trash2 />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="!loading && !filtered.length" class="empty-state">
          <Users />
          <div class="empty-state-title">没有匹配的用户</div>
        </div>
      </div>
    </div>

    <!-- 新建 / 编辑用户 -->
    <BaseModal v-model="userDialog" :title="userForm.id ? `编辑用户 · ${userForm.username}` : '新建用户'" :close-on-backdrop="false">
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label">用户名 <span class="text-danger">*</span></label>
          <input v-model="userForm.username" class="form-control" :disabled="!!userForm.id" placeholder="2-32 位" />
          <small v-if="userForm.id" class="form-hint">用户名由本人在「账号安全」中修改</small>
        </div>
        <div class="col-md-6">
          <label class="form-label">显示名称</label>
          <input v-model="userForm.display_name" class="form-control" placeholder="选填，例如：张三" maxlength="64" />
        </div>
        <div class="col-md-6">
          <label class="form-label">角色</label>
          <select v-model="userForm.role" class="form-select" :disabled="userForm.id === auth.userId">
            <option value="member">成员 · 按授权访问</option>
            <option value="admin">管理员 · 全部权限</option>
          </select>
        </div>
        <div class="col-md-6">
          <label class="form-label">{{ userForm.id ? '重置密码' : '初始密码' }} <span v-if="!userForm.id" class="text-danger">*</span></label>
          <input
            v-model="userForm.password"
            type="text"
            class="form-control"
            :placeholder="userForm.id ? '留空则不修改' : '至少 6 位'"
            autocomplete="new-password"
          />
        </div>
        <div v-if="userForm.id" class="col-12">
          <label class="option-card" :class="{ 'is-on': userForm.is_active, 'is-disabled': userForm.id === auth.userId }">
            <input v-model="userForm.is_active" class="form-check-input" type="checkbox" :disabled="userForm.id === auth.userId" />
            <span>
              <span class="option-card-title d-block">账号可用</span>
              <span class="option-card-desc d-block">取消勾选即禁用该账号，已登录的会话会立即失效</span>
            </span>
          </label>
        </div>
        <div v-if="userForm.id && userForm.role !== originalRole" class="col-12">
          <div class="callout warning">
            <TriangleAlert />
            <span>修改角色后，该用户需要重新登录。{{ userForm.role === 'admin' ? '管理员可以访问全部数据和系统设置。' : '降为成员后，只能访问分配给他的板块与记录。' }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-outline-secondary" @click="userDialog = false">取消</button>
        <button class="btn btn-primary" :disabled="savingUser" @click="saveUser">
          <span v-if="savingUser" class="spinner-border spinner-border-sm"></span>{{ userForm.id ? '保存修改' : '创建用户' }}
        </button>
      </template>
    </BaseModal>

    <!-- 板块权限 -->
    <BaseModal v-model="grantDrawer" :title="`板块权限 · ${grantUser?.display_name || grantUser?.username || ''}`" drawer width="760px">
      <div class="callout mb-3">
        <Info />
        <span>
          勾选可访问的板块。<strong>仅自己</strong>：只看到自己创建的和被分配的记录；<strong>全部记录</strong>：能看到板块内所有记录。
          自己创建的记录始终可以编辑和删除。
        </span>
      </div>

      <div class="grant-bar">
        <span class="toolbar-meta">已开通 <strong>{{ enabledGrantCount }}</strong> / {{ grantRows.length }} 个板块</span>
        <div class="d-flex gap-2">
          <button class="btn btn-sm btn-ghost" type="button" @click="setAll(true)">全部开通</button>
          <button class="btn btn-sm btn-ghost" type="button" @click="setAll(false)">全部关闭</button>
        </div>
      </div>

      <div v-if="grantLoading" class="py-4"><SkeletonTable :rows="5" :cols="4" /></div>
      <div v-else class="grant-list">
        <div v-for="row in grantRows" :key="row.module.id" class="grant-row" :class="{ on: row.enabled }">
          <label class="grant-main">
            <input v-model="row.enabled" class="form-check-input" type="checkbox" />
            <span class="name-ico sm"><AppIcon :name="row.module.icon" fallback="Database" /></span>
            <span class="name-text">
              <span class="name-title">{{ row.module.name }}</span>
              <span class="grant-sub">
                {{ categoryName(row.module.category_id) }}
                <template v-if="!row.module.is_enabled"> · <span class="text-danger">板块已禁用</span></template>
                <template v-if="row.shared"> · 已分配 {{ row.shared }} 条记录</template>
              </span>
            </span>
          </label>

          <div v-if="row.enabled" class="grant-opts">
            <div class="segmented">
              <button type="button" class="segmented-btn" :class="{ active: row.scope === 'own' }" @click="row.scope = 'own'">
                仅自己
              </button>
              <button type="button" class="segmented-btn" :class="{ active: row.scope === 'all' }" @click="row.scope = 'all'">
                全部记录
              </button>
            </div>
            <label class="grant-check">
              <input v-model="row.can_create" class="form-check-input" type="checkbox" />新增
            </label>
            <label class="grant-check" :class="{ disabled: row.scope !== 'all' }" v-tip="row.scope !== 'all' ? '仅在「全部记录」范围下生效' : ''">
              <input v-model="row.can_edit" class="form-check-input" type="checkbox" :disabled="row.scope !== 'all'" />编辑他人
            </label>
            <label class="grant-check" :class="{ disabled: row.scope !== 'all' }" v-tip="row.scope !== 'all' ? '仅在「全部记录」范围下生效' : ''">
              <input v-model="row.can_delete" class="form-check-input" type="checkbox" :disabled="row.scope !== 'all'" />删除他人
            </label>
          </div>
          <div v-else class="grant-off">{{ row.shared ? '未开通（仍可查看被分配的记录）' : '未开通' }}</div>
        </div>
        <div v-if="!grantRows.length" class="empty-state">
          <LayoutGrid />
          <div class="empty-state-title">还没有任何板块</div>
        </div>
      </div>

      <template #footer>
        <button class="btn btn-outline-secondary" @click="grantDrawer = false">取消</button>
        <button class="btn btn-primary" :disabled="savingGrants" @click="saveGrants">
          <span v-if="savingGrants" class="spinner-border spinner-border-sm"></span>保存权限
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  DoorOpen,
  Info,
  KeyRound,
  LayoutGrid,
  Search,
  ShieldCheck,
  SquarePen,
  Trash2,
  TriangleAlert,
  UserPlus,
  UserRound,
  Users,
  X,
} from 'lucide-vue-next'
import {
  authApi,
  categoryApi,
  moduleApi,
  userApi,
  type CategoryOut,
  type ModuleListItem,
  type UserOut,
  type UserRole,
} from '@/api'
import { useAuthStore } from '@/stores/auth'
import { toast, confirm } from '@/utils/ui'
import { vLoading } from '@/components/ui/loading'
import { vTip } from '@/components/ui/tooltip'
import BaseModal from '@/components/ui/BaseModal.vue'
import SkeletonTable from '@/components/ui/SkeletonTable.vue'
import { RouterLink } from 'vue-router'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppIcon from '@/components/AppIcon.vue'

const auth = useAuthStore()
const list = ref<UserOut[]>([])
const loading = ref(false)
const firstLoad = ref(true)
const keyword = ref('')
const roleFilter = ref<'all' | 'admin' | 'member' | 'disabled'>('all')
const allowRegister = ref(false)
const savingReg = ref(false)

const roleFilters = [
  { id: 'all', label: '全部' },
  { id: 'admin', label: '管理员' },
  { id: 'member', label: '成员' },
  { id: 'disabled', label: '已禁用' },
] as const

const adminCount = computed(() => list.value.filter((u) => u.role === 'admin').length)
const disabledCount = computed(() => list.value.filter((u) => !u.is_active).length)

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return list.value.filter((u) => {
    if (roleFilter.value === 'admin' && u.role !== 'admin') return false
    if (roleFilter.value === 'member' && u.role !== 'member') return false
    if (roleFilter.value === 'disabled' && u.is_active) return false
    if (!kw) return true
    return u.username.toLowerCase().includes(kw) || (u.display_name || '').toLowerCase().includes(kw)
  })
})

async function load() {
  loading.value = true
  try {
    const [{ data: users }, { data: settings }] = await Promise.all([userApi.list(), authApi.settings()])
    list.value = users
    allowRegister.value = settings.allow_register
  } finally {
    loading.value = false
    firstLoad.value = false
  }
}

async function toggleRegister(v: boolean) {
  savingReg.value = true
  try {
    const { data } = await authApi.updateSettings({ allow_register: v })
    allowRegister.value = data.allow_register
    toast(v ? '已开放注册' : '已关闭注册', 'success')
  } catch {
    allowRegister.value = !v
  } finally {
    savingReg.value = false
  }
}

/* ---------- 新建 / 编辑 ---------- */
const userDialog = ref(false)
const savingUser = ref(false)
const originalRole = ref<UserRole>('member')
const userForm = reactive({
  id: null as number | null,
  username: '',
  display_name: '',
  role: 'member' as UserRole,
  password: '',
  is_active: true,
})

function openCreate() {
  Object.assign(userForm, { id: null, username: '', display_name: '', role: 'member', password: '', is_active: true })
  originalRole.value = 'member'
  userDialog.value = true
}

function openEdit(u: UserOut) {
  Object.assign(userForm, {
    id: u.id,
    username: u.username,
    display_name: u.display_name || '',
    role: u.role,
    password: '',
    is_active: u.is_active,
  })
  originalRole.value = u.role
  userDialog.value = true
}

async function saveUser() {
  if (!userForm.id) {
    if (!userForm.username.trim() || userForm.password.length < 6) {
      toast('请填写用户名，密码至少 6 位', 'warning')
      return
    }
  } else if (userForm.password && userForm.password.length < 6) {
    toast('新密码至少 6 位', 'warning')
    return
  }
  savingUser.value = true
  try {
    if (userForm.id) {
      const target = list.value.find((u) => u.id === userForm.id)
      const payload: Record<string, any> = { display_name: userForm.display_name.trim() || null }
      if (target && userForm.role !== target.role) payload.role = userForm.role
      if (target && userForm.is_active !== target.is_active) payload.is_active = userForm.is_active
      if (userForm.password) payload.password = userForm.password
      await userApi.update(userForm.id, payload)
      toast('用户已更新', 'success')
    } else {
      await userApi.create({
        username: userForm.username.trim(),
        password: userForm.password,
        display_name: userForm.display_name.trim() || undefined,
        role: userForm.role,
      })
      toast('用户已创建', 'success')
    }
    userDialog.value = false
    await load()
  } finally {
    savingUser.value = false
  }
}

async function remove(u: UserOut) {
  const msg = `确定删除用户「${u.display_name || u.username}」？他创建的 ${u.owned_records} 条记录会保留，但变为无主记录（仅管理员可见）。`
  if (!(await confirm(msg, { title: '删除用户', confirmText: '确认删除', danger: true }))) return
  await userApi.remove(u.id)
  toast('用户已删除', 'success')
  await load()
}

/* ---------- 板块权限 ---------- */
interface GrantRow {
  module: ModuleListItem
  enabled: boolean
  scope: 'own' | 'all'
  can_create: boolean
  can_edit: boolean
  can_delete: boolean
  shared: number
}

const grantDrawer = ref(false)
const grantLoading = ref(false)
const savingGrants = ref(false)
const grantUser = ref<UserOut | null>(null)
const grantRows = ref<GrantRow[]>([])
const categories = ref<CategoryOut[]>([])

const enabledGrantCount = computed(() => grantRows.value.filter((r) => r.enabled).length)

function categoryName(id?: number | null) {
  return categories.value.find((c) => c.id === id)?.name || '未分类'
}

async function openGrants(u: UserOut) {
  grantUser.value = u
  grantDrawer.value = true
  grantLoading.value = true
  try {
    const [{ data: modules }, { data: grants }, { data: cats }] = await Promise.all([
      moduleApi.list(),
      userApi.grants(u.id),
      categoryApi.list(),
    ])
    categories.value = cats
    grantRows.value = modules.map((m) => {
      const g = grants.find((x) => x.module_id === m.id)
      const granted = !!g && g.granted !== false
      return {
        module: m,
        enabled: granted,
        scope: granted ? g!.scope : 'own',
        can_create: granted ? g!.can_create : true,
        can_edit: granted ? g!.can_edit : false,
        can_delete: granted ? g!.can_delete : false,
        shared: g?.shared_records || 0,
      }
    })
  } finally {
    grantLoading.value = false
  }
}

function setAll(v: boolean) {
  grantRows.value.forEach((r) => (r.enabled = v))
}

async function saveGrants() {
  if (!grantUser.value) return
  savingGrants.value = true
  try {
    await userApi.setGrants(
      grantUser.value.id,
      grantRows.value
        .filter((r) => r.enabled)
        .map((r) => ({
          module_id: r.module.id,
          scope: r.scope,
          can_create: r.can_create,
          can_edit: r.scope === 'all' && r.can_edit,
          can_delete: r.scope === 'all' && r.can_delete,
        }))
    )
    toast('权限已保存', 'success')
    grantDrawer.value = false
    await load()
  } finally {
    savingGrants.value = false
  }
}

/* ---------- 格式化 ---------- */
function initial(u: UserOut) {
  return (u.display_name || u.username).slice(0, 1).toUpperCase()
}

function formatDate(s: string) {
  return s ? new Date(s).toLocaleDateString('zh-CN') : ''
}

function formatRelative(s: string) {
  const d = new Date(s)
  const min = Math.floor((Date.now() - d.getTime()) / 60000)
  if (min < 1) return '刚才'
  if (min < 60) return `${min} 分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr} 小时前`
  const day = Math.floor(hr / 24)
  if (day < 30) return `${day} 天前`
  return d.toLocaleDateString('zh-CN')
}

onMounted(load)
</script>

<style scoped>
.reg-card {
  cursor: pointer;
}

.reg-pill {
  display: inline-flex;
  height: 36px;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius);
  background: var(--bg-elev);
  cursor: pointer;
}

.reg-inline-text {
  color: var(--ovh-navy-ink);
  font-size: 13px;
  font-weight: 500;
}

.reg-pill .form-switch {
  min-height: 0;
  padding-left: 0;
}

.reg-pill .form-switch .form-check-input {
  float: none;
  margin: 0;
}

.user-avatar {
  display: grid;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 7px;
  background: var(--bg-subtle);
  color: var(--text-soft);
  font-size: 12.5px;
  font-weight: 600;
}

.user-avatar.admin {
  background: var(--accent);
  color: var(--on-accent);
}

tr.is-disabled .name-title,
tr.is-disabled .user-avatar {
  opacity: 0.55;
}

.scope-text {
  color: var(--text-muted);
  font-size: 12.5px;
}

.scope-text strong {
  color: var(--text);
  font-weight: 600;
}

.dot-sep {
  margin: 0 7px;
  color: var(--text-faint);
}

/* ---------- 权限抽屉 ---------- */
.grant-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.grant-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.grant-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 16px;
  padding: 12px 14px;
  border: 1px solid var(--hairline);
  border-radius: var(--radius);
  background: var(--bg-elev);
  transition: border-color 0.15s ease, background 0.15s ease;
}

.grant-row.on {
  border-color: var(--accent-border);
  background: var(--accent-soft-subtle);
}

.grant-main {
  display: flex;
  min-width: 0;
  flex: 1 1 220px;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.grant-main .form-check-input {
  flex-shrink: 0;
  margin: 0;
}

.name-ico.sm {
  width: 30px;
  height: 30px;
  border-radius: var(--radius);
}

.name-ico.sm .lucide {
  width: 15px;
  height: 15px;
}

.grant-sub {
  overflow: hidden;
  color: var(--text-faint);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.grant-opts {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 14px;
}

.grant-check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-soft);
  font-size: 13px;
  cursor: pointer;
  user-select: none;
}

.grant-check .form-check-input {
  margin: 0;
}

.grant-check.disabled {
  color: var(--text-faint);
  cursor: not-allowed;
}

.grant-off {
  color: var(--text-faint);
  font-size: 12.5px;
}
</style>
