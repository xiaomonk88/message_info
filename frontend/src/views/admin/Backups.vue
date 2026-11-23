<template>
  <div class="page">
    <PageHeader
      title="数据备份"
      eyebrow="系统运维"
      subtitle="管理数据库与完整附件快照、本地导出下载与上传恢复、定时自动备份策略及 SFTP 异地容灾同步"
    >
      <template #links>
        <RouterLink to="/admin/users">用户与权限</RouterLink>
        <RouterLink to="/admin/audit">操作日志</RouterLink>
        <RouterLink to="/admin/account">账号安全</RouterLink>
      </template>
    </PageHeader>

    <!-- OVH 单行操作栏：左起钴蓝主按钮 + 次按钮 -->
    <div class="ovh-toolbar">
      <div class="toolbar-group">
        <button class="btn btn-primary" :disabled="creatingFull" @click="createFullBackup">
          <span v-if="creatingFull" class="spinner-border spinner-border-sm"></span>
          <Package v-else />创建完整备份
        </button>
        <button class="btn btn-outline-secondary" :disabled="creating" @click="createBackup">
          <span v-if="creating" class="spinner-border spinner-border-sm"></span>
          <Database v-else />仅数据库快照
        </button>
        <button class="btn btn-outline-secondary" :disabled="exportingLocal" @click="createAndDownloadFullBackup">
          <span v-if="exportingLocal" class="spinner-border spinner-border-sm"></span>
          <Download v-else />导出并下载到本地
        </button>
        <button class="btn btn-outline-primary" :disabled="uploading" @click="openUploadModal">
          <Upload />从本地上传恢复
        </button>
      </div>
      <div class="toolbar-group">
        <button class="btn btn-outline-secondary" @click="loadAll"><RotateCw />刷新状态</button>
      </div>
    </div>

    <!-- 极简一体式指标带 -->
    <div class="metric-strip">
      <button type="button" class="metric" @click="tab = 'snapshots'">
        <span class="metric-top">
          <span>本地快照</span>
          <ArrowUpRight class="metric-arrow" />
        </span>
        <span class="metric-value">{{ backups.length }}</span>
        <span class="metric-sub">合计 {{ formatSize(totalSize) }}</span>
      </button>
      <button type="button" class="metric" @click="tab = 'snapshots'">
        <span class="metric-top">
          <span>最近备份</span>
          <ArrowUpRight class="metric-arrow" />
        </span>
        <span class="metric-value is-text">{{ backups[0] ? formatTime(backups[0].created_at) : '尚未备份' }}</span>
        <span class="metric-sub">{{ backups[0] ? backupTypeText(backups[0].type) : '建议立即创建快照' }}</span>
      </button>
      <button type="button" class="metric" @click="tab = 'schedule'">
        <span class="metric-top">
          <span>定时备份</span>
          <ArrowUpRight class="metric-arrow" />
        </span>
        <span class="metric-value is-text">
          <span class="status-dot" :class="schedule.enabled ? 'on' : 'off'"></span>{{ schedule.enabled ? `每 ${schedule.interval_hours} 小时` : '未启用' }}
        </span>
        <span class="metric-sub">上次：{{ schedule.last_run_at ? formatTime(schedule.last_run_at) : '尚未执行' }}</span>
      </button>
      <button type="button" class="metric" @click="tab = 'sftp'">
        <span class="metric-top">
          <span>SFTP 异地容灾</span>
          <ArrowUpRight class="metric-arrow" />
        </span>
        <span class="metric-value is-text">
          <span class="status-dot" :class="sftpDotClass"></span>{{ sftp.enabled ? (sftp.last_status || '已启用') : '未启用' }}
        </span>
        <span class="metric-sub">上次同步：{{ sftp.last_sync_at ? formatTime(sftp.last_sync_at) : '尚未同步' }}</span>
      </button>
    </div>

    <div class="tabs-panel">
      <BaseTab v-model="tab">
        <!-- ============ 快照文件 ============ -->
        <BaseTabPane name="snapshots" label="快照文件" :badge="backups.length">
          <div class="ovh-toolbar">
            <div class="toolbar-group restore-group">
              <span class="toolbar-meta"><ArchiveRestore class="me-1" />从快照恢复</span>
              <select v-model="selectedFilename" class="form-select form-select-sm">
                <option value="">请选择备份快照文件…</option>
                <option v-for="item in backups" :key="item.filename" :value="item.filename">
                  {{ item.filename }} ({{ formatSize(item.size) }})
                </option>
              </select>
              <button
                class="btn btn-sm btn-danger"
                :disabled="!selectedFilename || restoring"
                @click="confirmRestore()"
              >
                <span v-if="restoring" class="spinner-border spinner-border-sm"></span>恢复快照
              </button>
              <button class="btn btn-sm btn-outline-primary" @click="openUploadModal">
                <Upload />上传本地备份
              </button>
            </div>
            <div class="toolbar-group">
              <button class="btn btn-sm btn-outline-danger" :disabled="!backups.length" @click="confirmDeleteAll">
                <Trash2 />一键清空
              </button>
            </div>
          </div>

          <div class="callout mb-2">
            <FolderArchive />
            <span>
              服务端存储目录：<code>data/backups/</code>（Docker 一键安装对应宿主机 <code>/opt/message_info/data/backups/</code>）。
              跨服务器迁移请使用<strong>完整备份 (.zip)</strong>，内含数据库、上传附件与字段加密密钥。
            </span>
          </div>

          <div class="callout warning mb-3">
            <TriangleAlert />
            <span>恢复操作会覆盖当前数据库中的所有记录；完整备份还会合并恢复附件目录并同步加密密钥。操作前建议先生成或下载一份最新快照。</span>
          </div>

          <div class="ovh-table-wrap">
            <SkeletonTable v-if="loading && firstLoad" :rows="5" :cols="5" />
            <div v-else class="table-responsive" v-loading="loading && !firstLoad">
              <table class="table table-hover align-middle">
                <thead>
                  <tr>
                    <th>备份文件</th>
                    <th style="width: 110px">类型</th>
                    <th class="text-end" style="width: 110px">大小</th>
                    <th style="width: 180px">备份时间</th>
                    <th class="text-end" style="width: 240px">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in backups" :key="row.filename">
                    <td>
                      <span class="name-cell">
                        <span class="name-ico" :class="{ full: row.type === 'full' }">
                          <Package v-if="row.type === 'full'" /><Database v-else />
                        </span>
                        <code class="code-mono">{{ row.filename }}</code>
                      </span>
                    </td>
                    <td>
                      <span class="badge" :class="row.type === 'full' ? 'text-bg-success' : 'text-bg-info'">
                        {{ backupTypeText(row.type) }}
                      </span>
                    </td>
                    <td class="text-end cell-mono">{{ formatSize(row.size) }}</td>
                    <td class="cell-mono cell-muted">{{ formatTime(row.created_at) }}</td>
                    <td class="text-end">
                      <div class="row-actions">
                        <button
                          class="btn btn-sm btn-outline-secondary"
                          :disabled="downloadingFile === row.filename"
                          @click="download(row.filename)"
                        >
                          <span v-if="downloadingFile === row.filename" class="spinner-border spinner-border-sm"></span>
                          <Download v-else />下载
                        </button>
                        <button
                          class="btn btn-sm btn-outline-primary"
                          :disabled="restoring"
                          @click="confirmRestore(row.filename)"
                        >
                          <ArchiveRestore />恢复
                        </button>
                        <button
                          class="btn btn-sm btn-outline-danger"
                          @click="confirmDelete(row.filename)"
                        >
                          <Trash2 />删除
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="!loading && !backups.length" class="empty-state">
                <FolderArchive />
                <div class="empty-state-title">暂无备份快照</div>
                <p>点击上方「创建完整备份」、「导出并下载到本地」，或「从本地上传恢复」导入已有备份文件。</p>
              </div>
            </div>
          </div>
        </BaseTabPane>

        <!-- ============ 定时备份 ============ -->
        <BaseTabPane name="schedule" label="定时备份">
          <div class="settings-row">
            <div>
              <h3 class="settings-row-title">自动备份</h3>
              <p class="settings-row-desc">开启后，后台调度器会在每个周期到达时自动创建一份数据库快照。修改后立即生效。</p>
            </div>
            <div>
              <label class="option-card" :class="{ 'is-on': schedule.enabled }" style="max-width: 460px">
                <input v-model="schedule.enabled" class="form-check-input" type="checkbox" @change="saveSchedule" />
                <span>
                  <span class="option-card-title d-block">{{ schedule.enabled ? '已启用定时自动备份' : '未启用定时自动备份' }}</span>
                  <span class="option-card-desc d-block">勾选即开启，取消即关闭</span>
                </span>
              </label>
            </div>
          </div>
          <div class="settings-row">
            <div>
              <h3 class="settings-row-title">备份周期</h3>
              <p class="settings-row-desc">两次自动备份之间的间隔，范围 1 – 720 小时。</p>
            </div>
            <div>
              <div class="d-flex align-items-center gap-2">
                <input
                  v-model.number="schedule.interval_hours"
                  type="number"
                  min="1"
                  max="720"
                  class="form-control"
                  style="width: 140px"
                  @change="saveSchedule"
                />
                <span class="text-muted">小时 / 次</span>
              </div>
            </div>
          </div>
          <div class="settings-row">
            <div>
              <h3 class="settings-row-title">执行记录</h3>
              <p class="settings-row-desc">调度器最近一次成功执行的时间。</p>
            </div>
            <div class="d-flex align-items-center gap-2">
              <span class="status-dot" :class="schedule.last_run_at ? 'on' : 'off'"></span>
              <span class="cell-mono">{{ schedule.last_run_at ? formatTime(schedule.last_run_at) : '尚未执行' }}</span>
            </div>
          </div>
        </BaseTabPane>

        <!-- ============ SFTP ============ -->
        <BaseTabPane name="sftp" label="SFTP 异地容灾">
          <div class="settings-row">
            <div>
              <h3 class="settings-row-title">启用状态</h3>
              <p class="settings-row-desc">将备份文件自动上传到远程服务器，防止本机损坏导致数据丢失。修改后需点击底部「保存设置」。</p>
            </div>
            <div class="d-flex flex-column gap-2" style="max-width: 560px">
              <label class="option-card" :class="{ 'is-on': sftp.enabled }">
                <input v-model="sftp.enabled" class="form-check-input" type="checkbox" />
                <span>
                  <span class="option-card-title d-block">启用 SFTP 异地容灾</span>
                  <span class="option-card-desc d-block">关闭时不会进行任何远程上传</span>
                </span>
              </label>
              <div class="d-flex flex-wrap gap-4 px-1">
                <div class="form-check">
                  <input id="uOnManual" v-model="sftp.upload_on_manual" class="form-check-input" type="checkbox" />
                  <label for="uOnManual" class="form-check-label">手动备份后自动上传</label>
                </div>
                <div class="form-check">
                  <input id="uOnSchedule" v-model="sftp.upload_on_schedule" class="form-check-input" type="checkbox" />
                  <label for="uOnSchedule" class="form-check-label">定时备份后自动上传</label>
                </div>
              </div>
            </div>
          </div>

          <div class="settings-row">
            <div>
              <h3 class="settings-row-title">服务器连接</h3>
              <p class="settings-row-desc">远程 SFTP 服务器的地址、端口、账号与存放目录。</p>
            </div>
            <div class="row g-3" style="max-width: 720px">
              <div class="col-md-8">
                <label class="form-label">主机地址</label>
                <input v-model="sftp.host" class="form-control" placeholder="1.2.3.4 或 remote.com" />
              </div>
              <div class="col-md-4">
                <label class="form-label">端口</label>
                <input v-model.number="sftp.port" type="number" min="1" max="65535" class="form-control" />
              </div>
              <div class="col-md-6">
                <label class="form-label">用户名</label>
                <input v-model="sftp.username" class="form-control" placeholder="backup_user" />
              </div>
              <div class="col-md-6">
                <label class="form-label">远程目标目录</label>
                <input v-model="sftp.remote_dir" class="form-control" placeholder="/data/backup" />
              </div>
            </div>
          </div>

          <div class="settings-row">
            <div>
              <h3 class="settings-row-title">身份认证</h3>
              <p class="settings-row-desc">已保存的密码 / 私钥不会回显，留空表示保留原设置。</p>
            </div>
            <div style="max-width: 720px">
              <div class="segmented mb-3">
                <button
                  type="button"
                  class="segmented-btn"
                  :class="{ active: sftp.auth_type === 'password' }"
                  @click="sftp.auth_type = 'password'"
                >
                  <KeyRound />密码认证
                </button>
                <button
                  type="button"
                  class="segmented-btn"
                  :class="{ active: sftp.auth_type === 'private_key' }"
                  @click="sftp.auth_type = 'private_key'"
                >
                  <FileKey />SSH 私钥认证
                </button>
              </div>

              <div v-if="sftp.auth_type === 'password'" style="max-width: 420px">
                <label class="form-label">
                  {{ sftp.has_password ? '密码（留空保留原设置）' : 'SFTP 密码' }}
                  <span v-if="sftp.has_password" class="badge text-bg-success ms-1">已保存</span>
                </label>
                <input v-model="sftp.password" type="password" class="form-control" autocomplete="new-password" />
              </div>
              <template v-else>
                <div class="mb-3">
                  <label class="form-label">
                    {{ sftp.has_private_key ? '私钥（留空保留原设置）' : 'SSH 私钥内容' }}
                    <span v-if="sftp.has_private_key" class="badge text-bg-success ms-1">已保存</span>
                  </label>
                  <textarea
                    v-model="sftp.private_key"
                    rows="4"
                    class="form-control font-monospace"
                    placeholder="-----BEGIN OPENSSH PRIVATE KEY-----"
                  ></textarea>
                </div>
                <div style="max-width: 420px">
                  <label class="form-label">
                    {{ sftp.has_private_key_passphrase ? '私钥密码短语（留空保留原值）' : '私钥口令（选填）' }}
                  </label>
                  <input v-model="sftp.private_key_passphrase" type="password" class="form-control" autocomplete="new-password" />
                </div>
              </template>
            </div>
          </div>

          <div class="settings-row">
            <div>
              <h3 class="settings-row-title">同步状态</h3>
              <p class="settings-row-desc">最近一次上传的结果。</p>
            </div>
            <div style="max-width: 720px">
              <ul class="kv-list sftp-status">
                <li>
                  <span class="kv-key">上次同步</span>
                  <span class="kv-val cell-mono">{{ sftp.last_sync_at ? formatTime(sftp.last_sync_at) : '尚未同步' }}</span>
                </li>
                <li>
                  <span class="kv-key">运行状态</span>
                  <span class="kv-val d-inline-flex align-items-center gap-2">
                    <span class="status-dot" :class="sftpDotClass"></span>
                    <span :class="{ 'text-danger': sftp.last_status === 'failed', 'text-success': sftp.last_status === 'success' }">
                      {{ sftp.last_status || '待机' }}
                    </span>
                  </span>
                </li>
                <li>
                  <span class="kv-key">同步文件</span>
                  <span class="kv-val cell-mono text-truncate" :title="sftp.last_filename || ''">{{ sftp.last_filename || '—' }}</span>
                </li>
              </ul>
              <div v-if="sftp.last_error" class="callout danger mt-2">
                <CircleAlert />
                <span class="text-break">{{ sftp.last_error }}</span>
              </div>
            </div>
          </div>

          <div class="sftp-actions">
            <button class="btn btn-outline-secondary" :disabled="testingSftp" @click="testSftp">
              <span v-if="testingSftp" class="spinner-border spinner-border-sm"></span>
              <PlugZap v-else />测试连接
            </button>
            <button class="btn btn-outline-secondary" :disabled="syncingSftp || !backups.length" @click="syncLatestSftp">
              <span v-if="syncingSftp" class="spinner-border spinner-border-sm"></span>
              <CloudUpload v-else />同步最新快照
            </button>
            <button class="btn btn-primary" :disabled="savingSftp" @click="saveSftp">
              <span v-if="savingSftp" class="spinner-border spinner-border-sm"></span>保存设置
            </button>
          </div>
        </BaseTabPane>
      </BaseTab>
    </div>

    <!-- ============ 本地上传备份恢复弹窗 ============ -->
    <BaseModal v-model="uploadModalOpen" title="从本地上传备份文件" :close-on-backdrop="!uploading">
      <div class="upload-box" :class="{ dragging: isDragging }" @dragover.prevent="isDragging = true" @dragleave.prevent="isDragging = false" @drop.prevent="onDropFile">
        <input
          ref="fileInputRef"
          type="file"
          accept=".zip,.db"
          class="d-none"
          @change="onPickFile"
        />
        <template v-if="!uploadFile">
          <Upload class="upload-ico" />
          <div class="upload-title">点击选择或拖拽备份文件到此处</div>
          <div class="upload-sub">支持完整备份 <code>.zip</code>（推荐，含附件与加密密钥）或数据库快照 <code>.db</code></div>
          <button type="button" class="btn btn-sm btn-outline-primary mt-2" @click="fileInputRef?.click()">
            选择本地文件
          </button>
        </template>
        <template v-else>
          <div class="picked-file">
            <span class="name-ico" :class="{ full: uploadFile.name.toLowerCase().endsWith('.zip') }">
              <Package v-if="uploadFile.name.toLowerCase().endsWith('.zip')" /><Database v-else />
            </span>
            <div class="picked-meta">
              <div class="code-mono text-break">{{ uploadFile.name }}</div>
              <div class="text-muted small">
                {{ formatSize(uploadFile.size) }} · {{ uploadFile.name.toLowerCase().endsWith('.zip') ? '完整备份 (.zip)' : '数据库快照 (.db)' }}
              </div>
            </div>
            <button type="button" class="btn btn-sm btn-outline-secondary ms-auto" :disabled="uploading" @click="fileInputRef?.click()">
              重选
            </button>
          </div>
        </template>
      </div>

      <div class="mt-3 d-flex flex-column gap-2">
        <label class="option-card" :class="{ 'is-on': uploadRestoreNow }">
          <input v-model="uploadRestoreNow" class="form-check-input" type="checkbox" :disabled="uploading" />
          <span>
            <span class="option-card-title d-block">上传后立即恢复数据（推荐）</span>
            <span class="option-card-desc d-block">
              {{ uploadRestoreNow ? '校验通过后立即覆盖恢复数据库（完整备份同时恢复上传附件与加密密钥）' : '仅将文件保存至服务端快照列表，稍后可手动点击「恢复」' }}
            </span>
          </span>
        </label>
      </div>

      <div v-if="uploadRestoreNow" class="callout warning mt-3 mb-0">
        <TriangleAlert />
        <span>立即恢复将覆盖当前系统中的全部记录；若从其他电脑/服务器迁移，恢复后可能需要使用原备份中的账号密码重新登录。</span>
      </div>

      <template #footer>
        <button type="button" class="btn btn-outline-secondary" :disabled="uploading" @click="uploadModalOpen = false">
          取消
        </button>
        <button
          type="button"
          class="btn"
          :class="uploadRestoreNow ? 'btn-danger' : 'btn-primary'"
          :disabled="!uploadFile || uploading"
          @click="submitUploadBackup"
        >
          <span v-if="uploading" class="spinner-border spinner-border-sm"></span>
          {{ uploadRestoreNow ? '上传并立即恢复' : '仅上传至列表' }}
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  ArchiveRestore,
  ArrowUpRight,
  CircleAlert,
  CloudUpload,
  Database,
  Download,
  FileKey,
  FolderArchive,
  KeyRound,
  Package,
  PlugZap,
  RotateCw,
  Trash2,
  TriangleAlert,
  Upload,
} from 'lucide-vue-next'
import { systemApi, type BackupFile, type SftpBackupConfig } from '@/api'
import { toast, confirm } from '@/utils/ui'
import { vLoading } from '@/components/ui/loading'
import SkeletonTable from '@/components/ui/SkeletonTable.vue'
import BaseTab from '@/components/ui/BaseTab.vue'
import BaseTabPane from '@/components/ui/BaseTabPane.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import { RouterLink } from 'vue-router'
import PageHeader from '@/components/ui/PageHeader.vue'

const backups = ref<BackupFile[]>([])
const loading = ref(false)
const firstLoad = ref(true)
const creating = ref(false)
const creatingFull = ref(false)
const exportingLocal = ref(false)
const downloadingFile = ref('')
const restoring = ref(false)
const savingSftp = ref(false)
const testingSftp = ref(false)
const syncingSftp = ref(false)
const selectedFilename = ref('')
const tab = ref('snapshots')

// 本地上传恢复状态
const uploadModalOpen = ref(false)
const uploadFile = ref<File | null>(null)
const uploadRestoreNow = ref(true)
const uploading = ref(false)
const isDragging = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

const schedule = reactive({ enabled: false, interval_hours: 24, last_run_at: null as string | null })
const sftp = reactive<SftpBackupConfig>({
  enabled: false,
  host: '',
  port: 22,
  username: '',
  auth_type: 'password',
  password: '',
  private_key: '',
  private_key_passphrase: '',
  remote_dir: '',
  upload_on_manual: true,
  upload_on_schedule: true,
  has_password: false,
  has_private_key: false,
  has_private_key_passphrase: false,
  last_sync_at: null,
  last_status: null,
  last_error: null,
  last_filename: null,
})

const totalSize = computed(() => backups.value.reduce((sum, b) => sum + (b.size || 0), 0))

const sftpDotClass = computed(() => {
  if (!sftp.enabled) return 'off'
  if (sftp.last_status === 'failed') return 'err'
  if (sftp.last_status === 'success') return 'on'
  return 'warn'
})

onMounted(loadAll)

async function loadAll() {
  loading.value = true
  try {
    const [{ data: list }, { data: scheduleData }, { data: sftpData }] = await Promise.all([
      systemApi.backups(),
      systemApi.backupSchedule(),
      systemApi.sftpConfig(),
    ])
    backups.value = list.items
    Object.assign(schedule, scheduleData)
    Object.assign(sftp, sftpData)
  } finally {
    loading.value = false
    firstLoad.value = false
  }
}

async function saveSftp() {
  savingSftp.value = true
  try {
    const { data } = await systemApi.updateSftpConfig(sftp)
    Object.assign(sftp, data)
    toast('SFTP 配置已保存', 'success')
  } finally {
    savingSftp.value = false
  }
}

async function testSftp() {
  await saveSftp()
  testingSftp.value = true
  try {
    await systemApi.testSftp()
    toast('SFTP 连接测试成功', 'success')
  } finally {
    testingSftp.value = false
  }
}

async function syncLatestSftp() {
  await saveSftp()
  syncingSftp.value = true
  try {
    await systemApi.syncLatestSftp()
    toast('最新快照已同步到 SFTP', 'success')
    const { data } = await systemApi.sftpConfig()
    Object.assign(sftp, data)
  } finally {
    syncingSftp.value = false
  }
}

async function createBackup() {
  creating.value = true
  try {
    const { data } = await systemApi.backup()
    toast(`数据库备份完成：${data.filename}`, 'success')
    await loadAll()
  } finally {
    creating.value = false
  }
}

async function createFullBackup() {
  creatingFull.value = true
  try {
    const { data } = await systemApi.fullBackup()
    toast(`完整备份完成：${data.filename}`, 'success')
    await loadAll()
  } finally {
    creatingFull.value = false
  }
}

async function createAndDownloadFullBackup() {
  exportingLocal.value = true
  try {
    const { data } = await systemApi.fullBackup()
    await loadAll()
    await download(data.filename)
    toast(`已导出并开始下载：${data.filename}`, 'success')
  } finally {
    exportingLocal.value = false
  }
}

async function saveSchedule() {
  const { data } = await systemApi.updateBackupSchedule({
    enabled: schedule.enabled,
    interval_hours: schedule.interval_hours,
  })
  Object.assign(schedule, data)
  toast('定时备份设置已保存', 'success')
}

async function confirmRestore(filename = selectedFilename.value) {
  if (!filename) return
  const item = backups.value.find((b) => b.filename === filename)
  const isFull = item?.type === 'full' || filename.toLowerCase().endsWith('.zip')
  const msg = isFull
    ? `确定恢复完整备份 ${filename}？当前数据库会被覆盖，附件目录与加密密钥将同步恢复。`
    : `确定恢复数据库备份 ${filename}？当前数据库会被覆盖。`
  if (!(await confirm(msg, { title: '恢复快照', confirmText: '确认恢复', danger: true }))) return
  restoring.value = true
  try {
    await systemApi.restoreBackup(filename)
    toast('快照恢复成功', 'success')
    await loadAll()
  } finally {
    restoring.value = false
  }
}

async function confirmDelete(filename: string) {
  if (!(await confirm(`确定删除快照 ${filename}？删除后不可恢复。`, { title: '删除备份', confirmText: '确认删除', danger: true }))) return
  await systemApi.deleteBackup(filename)
  toast('备份文件已删除', 'success')
  if (selectedFilename.value === filename) selectedFilename.value = ''
  await loadAll()
}

async function confirmDeleteAll() {
  if (!(await confirm(`确定删除全部 ${backups.value.length} 个备份文件？`, { title: '一键清空', confirmText: '确认清空', danger: true }))) return
  const { data } = await systemApi.deleteAllBackups()
  selectedFilename.value = ''
  if (data.skipped?.length) {
    toast(`已删除 ${data.deleted} 个，${data.skipped.length} 个文件正在使用已跳过`, 'warning')
  } else {
    toast(`已删除 ${data.deleted} 个备份文件`, 'success')
  }
  await loadAll()
}

async function download(filename: string) {
  downloadingFile.value = filename
  try {
    const { data } = await systemApi.downloadBackup(filename)
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } finally {
    downloadingFile.value = ''
  }
}

function openUploadModal() {
  uploadFile.value = null
  uploadRestoreNow.value = true
  isDragging.value = false
  if (fileInputRef.value) fileInputRef.value.value = ''
  uploadModalOpen.value = true
}

function setPickedFile(f?: File | null) {
  if (!f) return
  const lower = f.name.toLowerCase()
  if (!lower.endsWith('.zip') && !lower.endsWith('.db')) {
    toast('仅支持选择 .zip（完整备份）或 .db（数据库快照）文件', 'error')
    return
  }
  uploadFile.value = f
}

function onPickFile(e: Event) {
  const input = e.target as HTMLInputElement
  setPickedFile(input.files?.[0])
}

function onDropFile(e: DragEvent) {
  isDragging.value = false
  setPickedFile(e.dataTransfer?.files?.[0])
}

async function submitUploadBackup() {
  if (!uploadFile.value) return
  uploading.value = true
  try {
    const { data } = await systemApi.uploadBackup(uploadFile.value, uploadRestoreNow.value)
    uploadModalOpen.value = false
    if (data.restored) {
      toast(`已成功上传并恢复备份：${data.filename}`, 'success')
    } else {
      toast(`备份文件已上传至列表：${data.filename}`, 'success')
    }
    tab.value = 'snapshots'
    await loadAll()
  } finally {
    uploading.value = false
  }
}

function formatTime(s: string) {
  return s ? new Date(s).toLocaleString('zh-CN') : ''
}

function formatSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function backupTypeText(type?: string) {
  return type === 'full' ? '完整备份' : '数据库'
}
</script>

<style scoped>
.tabs-panel :deep(.nav-tabs) {
  margin-bottom: 16px !important;
}

.restore-group .form-select {
  width: 340px;
  max-width: 100%;
}

.restore-group .toolbar-meta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.restore-group .toolbar-meta .lucide {
  width: 14px;
  height: 14px;
}

.row-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.name-ico.full {
  border-color: var(--accent);
  background: var(--accent);
  color: var(--on-accent);
}

.upload-box {
  border: 1.5px dashed var(--surface-border, var(--hairline));
  border-radius: var(--radius);
  padding: 24px 20px;
  text-align: center;
  background: var(--bg-soft);
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.upload-box.dragging {
  border-color: var(--accent);
  background: var(--bg-elev);
}

.upload-ico {
  width: 28px;
  height: 28px;
  color: var(--accent);
  margin-bottom: 8px;
}

.upload-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.upload-sub {
  font-size: 13px;
  color: var(--text-muted);
}

.picked-file {
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
}

.picked-meta {
  min-width: 0;
}

.sftp-status {
  border: 1px solid var(--hairline);
  border-radius: var(--radius);
}

.sftp-status li {
  padding: 9px 14px;
}

.sftp-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 26px;
  border-top: 1px solid var(--hairline);
  background: var(--bg-soft);
}
</style>
