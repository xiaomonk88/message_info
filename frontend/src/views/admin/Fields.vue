<template>
  <div class="page">
    <PageHeader title="字段管理" eyebrow="结构配置" subtitle="定义全局可复用的元数据字段库，支持 Fernet 加密存储、检索过滤与数值汇总">
      <template #links>
        <RouterLink to="/admin/categories">1. 分类管理</RouterLink>
        <RouterLink to="/admin/modules">3. 板块管理</RouterLink>
      </template>
    </PageHeader>

    <div class="ovh-toolbar">
      <div class="toolbar-group">
        <button class="btn btn-primary" @click="openDialog()">
          <Plus />新建字段
        </button>
        <div class="segmented">
          <button
            v-for="grp in typeGroups"
            :key="grp.id"
            type="button"
            class="segmented-btn"
            :class="{ active: selectedGroup === grp.id }"
            @click="selectedGroup = grp.id"
          >
            {{ grp.label }}
          </button>
        </div>
      </div>
      <div class="toolbar-group">
        <div class="search-box">
          <Search />
          <input v-model="filterKeyword" class="form-control" placeholder="按编码、名称或说明搜索…" />
          <button v-if="filterKeyword" class="search-box-clear" type="button" aria-label="清除" @click="filterKeyword = ''">
            <X />
          </button>
        </div>
        <span class="toolbar-meta">共 <strong>{{ filteredList.length }}</strong> 个</span>
      </div>
    </div>

    <div class="ovh-table-wrap">
      <SkeletonTable v-if="loading && firstLoad" :rows="8" :cols="7" />
      <div v-else class="table-responsive" v-loading="loading && !firstLoad">
        <table class="table table-hover align-middle">
          <thead>
            <tr>
              <th style="width: 230px">字段</th>
              <th style="width: 120px">类型</th>
              <th style="width: 200px">能力</th>
              <th>字段说明</th>
              <th style="width: 240px">选项配置</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredList" :key="row.id" @dblclick="openDialog(row)">
              <td>
                <span class="name-text">
                  <span class="name-title">{{ row.name }}</span>
                  <span class="name-sub">{{ row.code }}</span>
                </span>
              </td>
              <td><span class="badge text-bg-secondary">{{ typeLabel(row.type) }}</span></td>
              <td>
                <div class="d-flex flex-wrap gap-1">
                  <span v-if="row.is_encrypted" class="badge text-bg-warning"><Lock />加密</span>
                  <span v-if="row.is_searchable" class="badge text-bg-success"><Search />可搜</span>
                  <span v-if="row.enable_summary" class="badge text-bg-primary"><Sigma />求和</span>
                  <span v-if="!row.is_encrypted && !row.is_searchable && !row.enable_summary" class="cell-faint">—</span>
                </div>
              </td>
              <td class="text-truncate cell-muted" style="max-width: 240px" :title="row.description || ''">
                {{ row.description || '—' }}
              </td>
              <td class="text-truncate cell-last" style="max-width: 240px">
                <code v-if="row.options" class="code-mono code-sm" :title="JSON.stringify(row.options)">
                  {{ JSON.stringify(row.options) }}
                </code>
                <span v-else class="cell-faint">—</span>
                <div class="row-float-actions" @dblclick.stop>
                  <button class="icon-button sm primary" v-tip="'编辑字段 (或双击行)'" @click="openDialog(row)">
                    <SquarePen />
                  </button>
                  <button class="icon-button sm danger" v-tip="'删除字段'" @click="remove(row)">
                    <Trash2 />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="!loading && !filteredList.length" class="empty-state">
          <ListPlus />
          <template v-if="list.length">
            <div class="empty-state-title">没有匹配的字段</div>
            <p>尝试更换关键词或类型筛选。</p>
          </template>
          <template v-else>
            <div class="empty-state-title">字段库为空</div>
            <p>先定义字段（如 IP 地址、账号、到期时间），再到板块中组合使用。</p>
            <button class="btn btn-primary btn-sm" @click="openDialog()"><Plus />新建字段</button>
          </template>
        </div>
      </div>
    </div>

    <!-- 新建 / 编辑字段 -->
    <BaseModal v-model="dialog" :title="form.id ? '编辑字段' : '新建字段'" size="lg" :close-on-backdrop="false">
      <div class="form-section">
        <div class="section-label"><Type />基本信息</div>
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">字段编码 <span class="text-danger">*</span></label>
            <input
              v-model="form.code"
              class="form-control"
              :disabled="!!form.id"
              placeholder="英文/数字/下划线，如 vps_ip"
            />
            <small v-if="form.id" class="form-hint">编码创建后不可修改</small>
          </div>
          <div class="col-md-6">
            <label class="form-label">字段名称 <span class="text-danger">*</span></label>
            <input v-model="form.name" class="form-control" placeholder="显示名称，如 IP地址" />
          </div>
          <div class="col-12">
            <label class="form-label">数据类型 <span class="text-danger">*</span></label>
            <select v-model="form.type" class="form-select" :disabled="!!form.id" @change="onTypeChange">
              <option v-for="t in types" :key="t.type" :value="t.type">
                {{ t.label }} ({{ t.type }}) — {{ t.description }}
              </option>
            </select>
            <small v-if="form.id" class="form-hint">数据类型创建后不可修改</small>
          </div>
        </div>
      </div>

      <div class="form-section">
        <div class="section-label"><Settings2 />字段能力</div>
        <div class="row g-2">
          <div class="col-md-4">
            <label
              class="option-card"
              :class="{ 'is-on': form.is_encrypted, 'is-disabled': form.type === 'password' }"
            >
              <input
                v-model="form.is_encrypted"
                class="form-check-input"
                type="checkbox"
                :disabled="form.type === 'password'"
              />
              <span>
                <span class="option-card-title d-block">Fernet 加密存储</span>
                <span class="option-card-desc d-block">数据库中以密文落盘{{ form.type === 'password' ? '（密码类型强制加密）' : '' }}</span>
              </span>
            </label>
          </div>
          <div class="col-md-4">
            <label
              class="option-card"
              :class="{ 'is-on': form.is_searchable, 'is-disabled': !canSearchType(form.type) || form.is_encrypted }"
            >
              <input
                v-model="form.is_searchable"
                class="form-check-input"
                type="checkbox"
                :disabled="!canSearchType(form.type) || form.is_encrypted"
              />
              <span>
                <span class="option-card-title d-block">支持搜索与筛选</span>
                <span class="option-card-desc d-block">参与关键词检索与多条件过滤（加密字段不可用）</span>
              </span>
            </label>
          </div>
          <div class="col-md-4">
            <label
              class="option-card"
              :class="{ 'is-on': form.enable_summary, 'is-disabled': form.type !== 'number' }"
            >
              <input
                v-model="form.enable_summary"
                class="form-check-input"
                type="checkbox"
                :disabled="form.type !== 'number'"
              />
              <span>
                <span class="option-card-title d-block">数值合计求和</span>
                <span class="option-card-desc d-block">列表底部显示合计，仅数值类型可用</span>
              </span>
            </label>
          </div>
        </div>
      </div>

      <div class="form-section">
        <div class="section-label"><Braces />说明与选项 <span class="section-label-hint">选填</span></div>
        <div class="mb-3">
          <label class="form-label">字段说明</label>
          <textarea v-model="form.description" class="form-control" rows="2" placeholder="录入时显示的帮助说明文字…"></textarea>
        </div>
        <div>
          <label class="form-label">选项配置（JSON）</label>
          <textarea
            v-model="form.optionsText"
            class="form-control font-monospace"
            rows="4"
            :placeholder="optionsHint"
          ></textarea>
          <small class="form-hint">{{ optionsHint }}</small>
        </div>
      </div>

      <template #footer>
        <button class="btn btn-outline-secondary" @click="dialog = false">取消</button>
        <button class="btn btn-primary" :disabled="saving" @click="save">
          <span v-if="saving" class="spinner-border spinner-border-sm"></span>保存字段
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  Braces,
  List,
  ListPlus,
  Lock,
  Plus,
  Search,
  Settings2,
  Sigma,
  SquarePen,
  Trash2,
  Type,
  X,
} from 'lucide-vue-next'
import { fieldApi, type FieldDef, type FieldType } from '@/api'
import { toast, confirm } from '@/utils/ui'
import { vLoading } from '@/components/ui/loading'
import { vTip } from '@/components/ui/tooltip'
import BaseModal from '@/components/ui/BaseModal.vue'
import SkeletonTable from '@/components/ui/SkeletonTable.vue'
import { RouterLink } from 'vue-router'
import PageHeader from '@/components/ui/PageHeader.vue'

const list = ref<FieldDef[]>([])
const types = ref<FieldType[]>([])
const loading = ref(false)
const firstLoad = ref(true)
const dialog = ref(false)
const saving = ref(false)
const filterKeyword = ref('')
const selectedGroup = ref('all')

const typeGroups = [
  { id: 'all', label: '全部' },
  { id: 'text', label: '文本/内容' },
  { id: 'number', label: '数值/时间' },
  { id: 'select', label: '选项/选择' },
  { id: 'media', label: '媒体/文件' },
  { id: 'secret', label: '凭据/密码' },
]

const form = reactive<any>({
  id: null,
  code: '',
  name: '',
  type: 'text',
  is_encrypted: false,
  is_searchable: true,
  enable_summary: false,
  description: '',
  optionsText: '',
})

const nonSearchableTypes = new Set(['password', 'image', 'file', 'json'])

const optionsHint = computed(() => {
  const examples: Record<string, string> = {
    text: '示例：{"maxLength": 100, "placeholder": "请输入..."}',
    textarea: '示例：{"rows": 4, "maxLength": 1000}',
    number: '示例：{"min": 0, "max": 9999, "precision": 2}',
    select: '示例：{"choices":[{"value":"a","label":"选项A"},{"value":"b","label":"选项B"}]}',
    multiselect: '同 select',
    image: '示例：{"maxSize": 5}，单位 MB',
    file: '示例：{"maxSize": 50}，单位 MB',
  }
  return examples[form.type] || '选填，无额外选项可留空'
})

const filteredList = computed(() => {
  let result = list.value
  const kw = filterKeyword.value.trim().toLowerCase()
  if (kw) {
    result = result.filter(
      (f) =>
        f.name.toLowerCase().includes(kw) ||
        f.code.toLowerCase().includes(kw) ||
        (f.description && f.description.toLowerCase().includes(kw))
    )
  }
  if (selectedGroup.value === 'text') {
    result = result.filter((f) => ['text', 'textarea', 'url', 'email', 'json'].includes(f.type))
  } else if (selectedGroup.value === 'number') {
    result = result.filter((f) => ['number', 'date', 'datetime', 'boolean'].includes(f.type))
  } else if (selectedGroup.value === 'select') {
    result = result.filter((f) => ['select', 'multiselect'].includes(f.type))
  } else if (selectedGroup.value === 'media') {
    result = result.filter((f) => ['image', 'file'].includes(f.type))
  } else if (selectedGroup.value === 'secret') {
    result = result.filter((f) => f.type === 'password' || f.is_encrypted)
  }
  return result
})

async function load() {
  loading.value = true
  try {
    const [{ data: fs }, { data: ts }] = await Promise.all([fieldApi.list(), fieldApi.types()])
    list.value = fs
    types.value = ts
  } finally {
    loading.value = false
    firstLoad.value = false
  }
}

function canSearchType(type: string) {
  return !nonSearchableTypes.has(type)
}

function defaultSearchable(type: string) {
  return canSearchType(type)
}

function typeLabel(t: string) {
  return types.value.find((x) => x.type === t)?.label || t
}

function onTypeChange() {
  if (form.type === 'password') form.is_encrypted = true
  if (!canSearchType(form.type) || form.is_encrypted) form.is_searchable = false
  else form.is_searchable = defaultSearchable(form.type)
  if (form.type !== 'number') form.enable_summary = false
}

function openDialog(row?: FieldDef) {
  if (row) {
    Object.assign(form, {
      id: row.id,
      code: row.code,
      name: row.name,
      type: row.type,
      is_encrypted: row.is_encrypted,
      is_searchable: row.is_searchable,
      enable_summary: row.enable_summary,
      description: row.description || '',
      optionsText: row.options ? JSON.stringify(row.options, null, 2) : '',
    })
  } else {
    Object.assign(form, {
      id: null,
      code: '',
      name: '',
      type: 'text',
      is_encrypted: false,
      is_searchable: true,
      enable_summary: false,
      description: '',
      optionsText: '',
    })
  }
  dialog.value = true
}

async function save() {
  if (!form.code || !form.name) {
    toast('请填写编码和名称', 'warning')
    return
  }
  let options: any = null
  if (form.optionsText.trim()) {
    try {
      options = JSON.parse(form.optionsText)
    } catch {
      toast('选项 JSON 格式错误', 'error')
      return
    }
  }
  const isSearchable = canSearchType(form.type) && !form.is_encrypted && form.is_searchable
  const enableSummary = form.type === 'number' && form.enable_summary
  saving.value = true
  try {
    if (form.id) {
      await fieldApi.update(form.id, {
        name: form.name,
        is_encrypted: form.is_encrypted,
        is_searchable: isSearchable,
        enable_summary: enableSummary,
        description: form.description,
        options,
      })
    } else {
      await fieldApi.create({
        code: form.code,
        name: form.name,
        type: form.type,
        is_encrypted: form.is_encrypted,
        is_searchable: isSearchable,
        enable_summary: enableSummary,
        description: form.description,
        options,
      })
    }
    toast('保存字段成功', 'success')
    dialog.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function remove(row: FieldDef) {
  if (!(await confirm(`确认删除字段「${row.name}」？若有板块引用该字段将不可删除。`, { danger: true }))) return
  await fieldApi.remove(row.id)
  toast('字段已删除', 'success')
  await load()
}

watch(() => form.is_encrypted, (v) => {
  if (v) form.is_searchable = false
})

watch(() => form.type, (v) => {
  if (v !== 'number') form.enable_summary = false
})

onMounted(load)
</script>
