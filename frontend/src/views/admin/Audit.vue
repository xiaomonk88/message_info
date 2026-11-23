<template>
  <div class="page">
    <PageHeader
      title="操作日志"
      eyebrow="系统运维"
      subtitle="实时审计系统登录、结构变更与记录增删改流水，支持按条数或天数自动清理"
    >
      <template #links>
        <RouterLink to="/admin/users">用户与权限</RouterLink>
        <RouterLink to="/admin/backups">数据备份</RouterLink>
        <RouterLink to="/admin/account">账号安全</RouterLink>
      </template>
    </PageHeader>

    <!-- OVH 单行工具栏：左起保留策略 + 清空；右起状态与刷新 -->
    <div class="ovh-toolbar">
      <div class="toolbar-group">
        <button class="btn btn-primary" @click="policyModal = true">
          <Settings2 />保留策略配置
        </button>
        <button class="btn btn-outline-danger" @click="clearLogs">
          <Trash2 />清空日志
        </button>
        <span class="toolbar-meta ms-1">
          <span class="status-dot" :class="settings.enabled ? 'on' : 'off'"></span>
          {{ settings.enabled ? '正在记录' : '已暂停记录' }}
          <span class="sep">·</span>
          上限 {{ settings.max_count || '不限' }} 条 / {{ settings.max_days || '不限' }} 天
        </span>
      </div>
      <div class="toolbar-group">
        <span class="toolbar-meta">共 <strong>{{ data.total }}</strong> 条</span>
        <button class="btn btn-outline-secondary px-2" type="button" v-tip="'刷新'" @click="loadLogs">
          <RotateCw />
        </button>
      </div>
    </div>

    <!-- OVH 无外框日志表 -->
    <div class="ovh-table-wrap">
      <SkeletonTable v-if="loading && firstLoad" :rows="10" :cols="6" />
      <template v-else>
        <div class="table-responsive" v-loading="loading && !firstLoad">
          <table class="table table-hover align-middle">
            <thead>
              <tr>
                <th class="text-center" style="width: 72px">#</th>
                <th style="width: 180px">操作时间</th>
                <th style="width: 120px">动作</th>
                <th style="width: 130px">对象类型</th>
                <th class="text-end" style="width: 84px">实体 ID</th>
                <th style="width: 110px">操作人</th>
                <th>摘要详情</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in data.items" :key="row.id">
                <td class="text-center cell-mono cell-faint">{{ row.id }}</td>
                <td class="cell-mono cell-muted">{{ formatTime(row.created_at) }}</td>
                <td><span class="badge badge-dot" :class="actionBadge(row.action)">{{ row.action }}</span></td>
                <td><code class="code-sm">{{ row.entity_type }}</code></td>
                <td class="text-end cell-mono">{{ row.entity_id ?? '—' }}</td>
                <td>
                  <span class="actor">
                    <span class="actor-avatar">{{ String(row.actor || '?').slice(0, 1).toUpperCase() }}</span>
                    {{ row.actor }}
                  </span>
                </td>
                <td class="text-truncate cell-muted" style="max-width: 420px" :title="row.summary">
                  {{ row.summary }}
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="!loading && !data.items.length" class="empty-state">
            <History />
            <div class="empty-state-title">暂无操作日志</div>
          </div>
        </div>
        <div class="mt-3">
          <BasePagination :total="data.total" :page="page" :page-size="50" @update:page="onPage" />
        </div>
      </template>
    </div>

    <!-- 保留策略弹窗 -->
    <BaseModal v-model="policyModal" title="日志记录与保留策略">
      <div class="settings-row pt-0">
        <div>
          <div class="settings-row-title">开启日志记录</div>
          <div class="settings-row-desc">记录增删改、备份与登录等关键系统操作</div>
        </div>
        <div class="form-check form-switch mb-0">
          <input id="auditEnabled" v-model="settings.enabled" class="form-check-input" type="checkbox" role="switch" />
        </div>
      </div>
      <div class="row g-3 pt-3">
        <div class="col-sm-6">
          <label class="form-label" for="auditMaxCount">最大保留条数</label>
          <input
            id="auditMaxCount"
            v-model.number="settings.max_count"
            type="number"
            min="0"
            max="1000000"
            class="form-control"
          />
          <small class="form-hint">填 0 表示不限制条数</small>
        </div>
        <div class="col-sm-6">
          <label class="form-label" for="auditMaxDays">最大保留天数</label>
          <input
            id="auditMaxDays"
            v-model.number="settings.max_days"
            type="number"
            min="0"
            max="36500"
            class="form-control"
          />
          <small class="form-hint">填 0 表示不限制天数</small>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-outline-secondary" @click="policyModal = false">取消</button>
        <button class="btn btn-primary" :disabled="savingSettings" @click="saveSettings">
          <span v-if="savingSettings" class="spinner-border spinner-border-sm"></span>保存策略
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { History, RotateCw, Settings2, Trash2 } from 'lucide-vue-next'
import { systemApi, type AuditSettings } from '@/api'
import { toast, confirm } from '@/utils/ui'
import { vLoading } from '@/components/ui/loading'
import { vTip } from '@/components/ui/tooltip'
import BaseModal from '@/components/ui/BaseModal.vue'
import BasePagination from '@/components/ui/BasePagination.vue'
import SkeletonTable from '@/components/ui/SkeletonTable.vue'
import { RouterLink } from 'vue-router'
import PageHeader from '@/components/ui/PageHeader.vue'

const data = reactive<{ items: any[]; total: number }>({ items: [], total: 0 })
const settings = reactive<AuditSettings>({ enabled: true, max_count: 5000, max_days: 180 })
const loading = ref(false)
const firstLoad = ref(true)
const savingSettings = ref(false)
const policyModal = ref(false)
const page = ref(1)

function actionKind(action: string): string {
  if (/create|add|login|restore/i.test(action)) return 'create'
  if (/delete|purge|clear|remove/i.test(action)) return 'delete'
  if (/update|edit|change|reorder/i.test(action)) return 'update'
  return 'other'
}

function actionBadge(action: string): string {
  const k = actionKind(action)
  if (k === 'create') return 'text-bg-success'
  if (k === 'delete') return 'text-bg-danger'
  if (k === 'update') return 'text-bg-warning'
  return 'text-bg-info'
}

async function loadLogs() {
  loading.value = true
  try {
    const { data: d } = await systemApi.audit({ page: page.value, page_size: 50 })
    data.items = d.items
    data.total = d.total
  } finally {
    loading.value = false
    firstLoad.value = false
  }
}

function onPage(p: number) {
  page.value = p
  loadLogs()
}

async function loadSettings() {
  const { data } = await systemApi.auditSettings()
  Object.assign(settings, data)
}

async function saveSettings() {
  savingSettings.value = true
  try {
    const { data } = await systemApi.updateAuditSettings(settings)
    Object.assign(settings, data)
    toast('日志策略已保存', 'success')
    policyModal.value = false
    page.value = 1
    await loadLogs()
  } finally {
    savingSettings.value = false
  }
}

async function clearLogs() {
  if (!(await confirm('确定清空全部操作日志记录？此操作不可撤销', { danger: true }))) return
  const { data: result } = await systemApi.clearAuditLogs()
  toast(`已清空 ${result.deleted} 条日志`, 'success')
  page.value = 1
  await loadLogs()
}

function formatTime(s: string) {
  return s ? new Date(s).toLocaleString('zh-CN') : ''
}

onMounted(async () => {
  await Promise.all([loadSettings(), loadLogs()])
})
</script>

<style scoped>
.sep {
  margin: 0 4px;
  color: var(--text-faint);
}

.actor {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--text-soft);
}

.actor-avatar {
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  border-radius: 6px;
  background: var(--bg-subtle);
  color: var(--text-soft);
  font-size: 11px;
  font-weight: 600;
}
</style>
