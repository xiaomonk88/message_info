<template>
  <div class="page">
    <PageHeader
      title="账号安全"
      eyebrow="系统运维"
      subtitle="管理当前登录账号的用户名、登录密码凭据以及系统级数据清理"
    >
      <template v-if="auth.isAdmin" #links>
        <RouterLink to="/admin/users">用户与权限</RouterLink>
        <RouterLink to="/admin/backups">数据备份</RouterLink>
        <RouterLink to="/admin/audit">操作日志</RouterLink>
      </template>
    </PageHeader>

    <!-- 现代单列设置流（最大 720px，清爽舒展） -->
    <div class="settings-stream">
      <!-- 当前账号概览 -->
      <div class="acc-profile">
        <span class="acc-avatar">{{ (auth.username || '管').slice(0, 1).toUpperCase() }}</span>
        <div class="acc-info">
          <div class="acc-name">{{ auth.username || '管理员' }}</div>
          <div class="acc-meta">{{ auth.isAdmin ? '系统管理员' : '普通成员' }} · 当前会话在线</div>
        </div>
      </div>

      <!-- 修改用户名 & 修改密码（左右两列横排） -->
      <div class="row g-3">
        <div class="col-lg-6">
          <section class="panel cred-panel">
            <div class="panel-head">
              <div>
                <div class="panel-title">修改用户名</div>
                <div class="panel-desc">当前用户名 <code>{{ auth.username }}</code>，长度需在 2–64 个字符之间</div>
              </div>
            </div>
            <div class="panel-body cred-body">
              <div class="row g-3">
                <div class="col-sm-6">
                  <label class="form-label">新用户名</label>
                  <input v-model="userForm.new_username" class="form-control" placeholder="2–64 个字符" maxlength="64" />
                </div>
                <div class="col-sm-6">
                  <label class="form-label">当前密码</label>
                  <input
                    v-model="userForm.password"
                    type="password"
                    class="form-control"
                    placeholder="输入当前密码核验身份"
                    autocomplete="current-password"
                    @keyup.enter="submitUsername"
                  />
                </div>
              </div>
            </div>
            <div class="stream-foot">
              <span class="stream-tip">修改成功后自动退出，需使用新用户名重新登录</span>
              <button class="btn btn-primary btn-sm" :disabled="savingUser" @click="submitUsername">
                <span v-if="savingUser" class="spinner-border spinner-border-sm"></span>保存用户名
              </button>
            </div>
          </section>
        </div>

        <div class="col-lg-6">
          <section class="panel cred-panel">
            <div class="panel-head">
              <div>
                <div class="panel-title">修改登录密码</div>
                <div class="panel-desc">至少 6 位，建议混合字母、数字与符号</div>
              </div>
              <div v-if="form.new_password" class="pwd-meter">
                <div class="pwd-meter-bar">
                  <span v-for="i in 4" :key="i" :class="{ on: i <= pwdScore }" :data-level="pwdScore"></span>
                </div>
                <span class="pwd-meter-text">{{ pwdLabel }}</span>
              </div>
            </div>
            <div class="panel-body cred-body">
              <div class="row g-3">
                <div class="col-sm-4">
                  <label class="form-label">原密码</label>
                  <input v-model="form.old_password" type="password" class="form-control" placeholder="当前密码" autocomplete="current-password" />
                </div>
                <div class="col-sm-4">
                  <label class="form-label">新密码</label>
                  <input v-model="form.new_password" type="password" class="form-control" placeholder="至少 6 位" autocomplete="new-password" />
                </div>
                <div class="col-sm-4">
                  <label class="form-label">确认新密码</label>
                  <input
                    v-model="form.confirm"
                    type="password"
                    class="form-control"
                    :class="{ 'is-invalid': form.confirm && form.confirm !== form.new_password }"
                    placeholder="再次输入"
                    autocomplete="new-password"
                    @keyup.enter="submit"
                  />
                </div>
              </div>
            </div>
            <div class="stream-foot">
              <span class="stream-tip">修改成功后自动退出，需使用新密码重新登录</span>
              <button class="btn btn-primary btn-sm" :disabled="saving" @click="submit">
                <span v-if="saving" class="spinner-border spinner-border-sm"></span>保存密码
              </button>
            </div>
          </section>
        </div>
      </div>

      <!-- 危险操作区（管理员） -->
      <section v-if="auth.isAdmin" class="panel danger-panel">
        <div class="panel-head">
          <div>
            <div class="panel-title text-danger">危险操作</div>
            <div class="panel-desc">以下操作不可撤销，执行前请先前往数据备份生成快照</div>
          </div>
          <RouterLink to="/admin/backups" class="btn btn-sm btn-outline-secondary">
            <Archive />去备份
          </RouterLink>
        </div>
        <div class="danger-list">
          <div class="danger-row">
            <div>
              <div class="danger-title">清空全部记录</div>
              <div class="danger-desc">
                删除全部业务记录（含回收站）与上传附件，保留分类、字段与板块结构。
              </div>
            </div>
            <button class="btn btn-sm btn-outline-danger" @click="openClearRecords">清空记录</button>
          </div>
          <div class="danger-row">
            <div>
              <div class="danger-title">清空全部数据 · 工厂重置</div>
              <div class="danger-desc">
                抹除记录、板块、字段、分类、日志及上传文件，恢复初始空白状态。
              </div>
            </div>
            <button class="btn btn-sm btn-danger" @click="openClearAll">工厂重置</button>
          </div>
        </div>
      </section>
    </div>

    <!-- 高危操作确认 -->
    <BaseModal v-model="dangerDialog" :title="danger.title" :close-on-backdrop="false">
      <div class="callout danger mb-3">
        <TriangleAlert />
        <div>
          <strong class="text-danger d-block">{{ danger.title }}</strong>
          该操作具有破坏性且无法撤销，请确认已经做好数据备份。
        </div>
      </div>
      <ul class="danger-bullets">
        <li v-for="(line, i) in danger.bullets" :key="i">{{ line }}</li>
      </ul>
      <div class="pt-3 border-top">
        <label class="form-label">请输入大写 <code class="text-danger">YES</code> 以确认：</label>
        <input
          v-model="danger.input"
          class="form-control"
          placeholder="YES"
          :disabled="danger.loading"
          @keyup.enter="confirmDanger"
        />
      </div>
      <template #footer>
        <button class="btn btn-outline-secondary" :disabled="danger.loading" @click="dangerDialog = false">取消</button>
        <button class="btn btn-danger" :disabled="danger.loading || danger.input !== 'YES'" @click="confirmDanger">
          <span v-if="danger.loading" class="spinner-border spinner-border-sm"></span>确认执行
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Archive, TriangleAlert } from 'lucide-vue-next'
import { authApi, systemApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useNavStore } from '@/stores/nav'
import { toast, alert } from '@/utils/ui'
import BaseModal from '@/components/ui/BaseModal.vue'
import PageHeader from '@/components/ui/PageHeader.vue'

const auth = useAuthStore()
const nav = useNavStore()
const saving = ref(false)
const savingUser = ref(false)
const form = reactive({ old_password: '', new_password: '', confirm: '' })
const userForm = reactive({ new_username: '', password: '' })

const pwdScore = computed(() => {
  const p = form.new_password
  if (!p) return 0
  let s = 0
  if (p.length >= 6) s++
  if (p.length >= 10) s++
  if (/[a-z]/i.test(p) && /\d/.test(p)) s++
  if (/[^a-z0-9]/i.test(p)) s++
  return Math.max(1, s)
})
const pwdLabel = computed(() => ['', '弱', '一般', '较强', '强'][pwdScore.value])

async function submitUsername() {
  const newName = userForm.new_username.trim()
  if (!newName) {
    toast('请输入新用户名', 'warning')
    return
  }
  if (newName.length < 2 || newName.length > 64) {
    toast('用户名长度需 2-64 字符', 'error')
    return
  }
  if (!userForm.password) {
    toast('请输入当前密码以验证身份', 'warning')
    return
  }
  if (newName === auth.username) {
    toast('新用户名与当前相同', 'error')
    return
  }
  savingUser.value = true
  try {
    await authApi.changeUsername(userForm.password, newName)
    toast('用户名已修改，请使用新用户名重新登录', 'success')
    auth.logout()
    location.href = '/login'
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.message || '修改失败'
    toast(msg, 'error')
  } finally {
    savingUser.value = false
  }
}

async function submit() {
  if (!form.old_password || !form.new_password) {
    toast('请填写密码', 'warning')
    return
  }
  if (form.new_password !== form.confirm) {
    toast('两次输入的新密码不一致', 'error')
    return
  }
  if (form.new_password.length < 6) {
    toast('新密码至少 6 位', 'error')
    return
  }
  saving.value = true
  try {
    await authApi.changePassword(form.old_password, form.new_password)
    toast('密码已修改，请重新登录', 'success')
    auth.logout()
    location.href = '/login'
  } finally {
    saving.value = false
  }
}

type DangerKind = 'records' | 'all'

const dangerDialog = ref(false)
const danger = reactive({
  kind: 'records' as DangerKind,
  title: '',
  bullets: [] as string[],
  input: '',
  loading: false,
})

function openClearRecords() {
  danger.kind = 'records'
  danger.title = '清空全部记录'
  danger.bullets = [
    '删除所有板块下的全部记录数据（包含回收站中的记录）',
    '删除 data/uploads/ 目录下全部上传的图片和附件文件',
    '保留分类、字段、板块结构，结构不变可继续录入使用',
    '操作不可恢复，建议先到「数据备份」页生成一份完整备份',
  ]
  danger.input = ''
  dangerDialog.value = true
}

function openClearAll() {
  danger.kind = 'all'
  danger.title = '清空全部数据 · 工厂重置'
  danger.bullets = [
    '删除全部记录、回收站数据',
    '删除全部板块及其字段配置',
    '删除全部全局字段定义',
    '删除全部分类',
    '清空全部操作日志',
    '删除 data/uploads/ 目录下全部上传文件',
    '保留项：管理员账号、历史备份文件（data/backups/）、SFTP 配置',
    '操作完成后系统将回到初次安装时的纯净状态',
  ]
  danger.input = ''
  dangerDialog.value = true
}

async function confirmDanger() {
  if (danger.input !== 'YES') {
    toast('请输入大写 YES 以确认', 'warning')
    return
  }
  danger.loading = true
  try {
    if (danger.kind === 'records') {
      const { data } = await systemApi.clearAllRecords(danger.input)
      toast(`已清空 ${data.deleted_records} 条记录 · 删除 ${data.deleted_uploads} 项上传文件`, 'success')
    } else {
      const { data } = await systemApi.clearAllData(danger.input)
      await alert(
        `已清空：记录 ${data.deleted_records} · 板块 ${data.deleted_modules} · 字段 ${data.deleted_fields} · 分类 ${data.deleted_categories} · 上传 ${data.deleted_uploads}。系统已回到初始状态。`,
        { title: '工厂重置完成', type: 'success', confirmText: '知道了' }
      )
    }
    dangerDialog.value = false
    await nav.refresh()
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.message || '操作失败'
    toast(msg, 'error')
  } finally {
    danger.loading = false
  }
}
</script>

<style scoped>
.settings-stream {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cred-panel {
  display: flex;
  height: 100%;
  flex-direction: column;
}

.cred-body {
  flex: 1 1 auto;
}

.acc-profile {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-card);
  background: var(--bg-elev);
  box-shadow: var(--shadow-card);
}

.acc-avatar {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border-radius: 50%;
  background: var(--ovh-ice);
  color: var(--ovh-navy);
  font-size: 16px;
  font-weight: 700;
}

.acc-name {
  color: var(--text);
  font-size: 16px;
  font-weight: 600;
}

.acc-meta {
  color: var(--text-muted);
  font-size: 13px;
}

.stream-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 20px;
  border-top: 1px solid var(--hairline);
  background: var(--bg-soft);
}

.stream-tip {
  color: var(--text-faint);
  font-size: 12px;
}

.pwd-meter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pwd-meter-bar {
  display: grid;
  width: 84px;
  grid-template-columns: repeat(4, 1fr);
  gap: 3px;
}

.pwd-meter-bar span {
  height: 4px;
  border-radius: 2px;
  background: var(--bg-subtle);
}

.pwd-meter-bar span.on[data-level='1'] { background: var(--danger); }
.pwd-meter-bar span.on[data-level='2'] { background: var(--warning-dot); }
.pwd-meter-bar span.on[data-level='3'] { background: var(--info); }
.pwd-meter-bar span.on[data-level='4'] { background: var(--success-dot); }

.pwd-meter-text {
  color: var(--text-muted);
  font-size: 11.5px;
}

.danger-panel {
  border-color: var(--danger-border);
}

.danger-list {
  display: flex;
  flex-direction: column;
}

.danger-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--hairline);
}

.danger-row:last-child {
  border-bottom: 0;
}

.danger-row .btn {
  flex-shrink: 0;
}

.danger-title {
  color: var(--text);
  font-size: 14px;
  font-weight: 600;
}

.danger-desc {
  margin-top: 2px;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.5;
}

.danger-bullets {
  margin: 0 0 16px;
  padding-left: 18px;
  color: var(--text-soft);
  font-size: 13px;
  line-height: 1.75;
}

@media (max-width: 575.98px) {
  .danger-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
