<template>
  <div class="page">
    <PageHeader title="板块管理" eyebrow="结构配置" subtitle="装配业务数据表结构、关联字段库并定义计算公式列">
      <template #links>
        <RouterLink to="/admin/categories">1. 分类管理</RouterLink>
        <RouterLink to="/admin/fields">2. 字段管理</RouterLink>
      </template>
    </PageHeader>

    <div class="ovh-toolbar">
      <div class="toolbar-group">
        <button class="btn btn-primary" @click="openDialog()">
          <Plus />新建板块
        </button>
        <span class="toolbar-meta ms-1">共 <strong>{{ list.length }}</strong> 个板块</span>
      </div>
      <div class="toolbar-group">
        <div class="search-box">
          <Search />
          <input v-model="keyword" class="form-control" placeholder="按名称、编码或分类搜索…" />
          <button v-if="keyword" class="search-box-clear" type="button" aria-label="清除" @click="keyword = ''">
            <X />
          </button>
        </div>
      </div>
    </div>

    <div class="ovh-table-wrap">
      <SkeletonTable v-if="loading && firstLoad" :rows="8" :cols="8" />
      <div v-else class="table-responsive" v-loading="loading && !firstLoad">
        <table class="table table-hover align-middle">
          <thead>
            <tr>
              <th style="width: 220px">板块</th>
              <th style="width: 110px">分类</th>
              <th class="text-end" style="width: 68px">字段</th>
              <th class="text-end" style="width: 80px">记录</th>
              <th class="text-end" style="width: 64px">排序</th>
              <th style="width: 80px">状态</th>
              <th style="width: 80px">图片</th>
              <th>说明</th>
              <th class="text-end" style="width: 240px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredList" :key="row.id" @dblclick="openDialog(row)">
              <td>
                <span class="name-cell">
                  <span class="name-ico"><AppIcon :name="row.icon" fallback="Database" /></span>
                  <span class="name-text">
                    <span class="name-title">{{ row.name }}</span>
                    <span class="name-sub">{{ row.code }}</span>
                  </span>
                </span>
              </td>
              <td><span class="badge badge-purple">{{ categoryName(row.category_id) }}</span></td>
              <td class="text-end cell-mono">{{ row.field_count }}</td>
              <td class="text-end cell-mono fw-semibold text-primary">
                <RouterLink :to="`/m/${row.id}`" class="text-decoration-none" @dblclick.stop>{{ row.record_count }}</RouterLink>
              </td>
              <td class="text-end cell-mono">{{ row.sort_order }}</td>
              <td>
                <span class="badge badge-dot" :class="row.is_enabled ? 'text-bg-success' : 'text-bg-secondary'">
                  {{ row.is_enabled ? '启用' : '禁用' }}
                </span>
              </td>
              <td>
                <span class="badge" :class="row.auto_load_images ? 'text-bg-success' : 'text-bg-info'">
                  {{ row.auto_load_images ? '自动' : '手动' }}
                </span>
              </td>
              <td class="text-truncate cell-muted" style="max-width: 220px" :title="row.description || ''">
                <span>{{ row.description || '—' }}</span>
              </td>
              <td class="text-end" @dblclick.stop>
                <div class="row-actions">
                  <button class="btn btn-sm btn-outline-secondary" v-tip="'进入板块查看数据'" @click="$router.push(`/m/${row.id}`)">
                    <ExternalLink />数据
                  </button>
                  <button class="btn btn-sm btn-outline-primary" v-tip="'以此板块为模板复制新建'" @click="duplicateModule(row)">
                    <Copy />复制
                  </button>
                  <button class="btn btn-sm btn-outline-secondary" v-tip="'编辑板块配置 (或双击行)'" @click="openDialog(row)">
                    <SquarePen />编辑
                  </button>
                  <button class="btn btn-sm btn-outline-danger" v-tip="'删除板块'" @click="remove(row)">
                    <Trash2 />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="!loading && !filteredList.length" class="empty-state">
          <LayoutGrid />
          <template v-if="list.length">
            <div class="empty-state-title">没有匹配的板块</div>
          </template>
          <template v-else>
            <div class="empty-state-title">暂无业务板块</div>
            <p>板块是存放记录的数据表。新建后在「字段配置」中从字段库挑选字段即可。</p>
            <button class="btn btn-primary btn-sm" @click="openDialog()"><Plus />新建板块</button>
          </template>
        </div>
      </div>
    </div>

    <!-- 新建 / 复制 / 编辑板块 -->
    <BaseModal
      v-model="dialog"
      :title="modalTitle"
      size="xl"
      :close-on-backdrop="false"
    >
      <div v-if="copySource" class="callout mb-3">
        <Copy />
        <span>
          正在基于板块 <strong>{{ copySource.name }}</strong>（<code>{{ copySource.code }}</code>）复制创建新板块，已自动带入全部
          <strong>{{ form.fields.length }}</strong> 个字段配置与 <strong>{{ form.calculated_fields.length }}</strong> 个计算字段。请修改新板块的编码与名称后保存。
        </span>
      </div>

      <BaseTab v-model="tab">
        <BaseTabPane name="base" label="基础信息">
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label">编码 <span class="text-danger">*</span></label>
              <input v-model="form.code" class="form-control" :disabled="!!form.id" placeholder="英文/数字/下划线，如 server_list" />
              <small v-if="form.id" class="form-hint">编码创建后不可修改</small>
              <small v-else-if="copySource" class="form-hint">需以字母开头，仅含字母、数字或下划线（不可与现有板块重名）</small>
            </div>
            <div class="col-md-6">
              <label class="form-label">名称 <span class="text-danger">*</span></label>
              <input v-model="form.name" class="form-control" placeholder="如：服务器资产" />
            </div>
            <div class="col-md-6">
              <label class="form-label">所属分类</label>
              <select v-model="form.category_id" class="form-select">
                <option :value="null">（无分类）</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="col-md-6">
              <label class="form-label">显示排序</label>
              <input v-model.number="form.sort_order" type="number" min="0" class="form-control" />
            </div>
            <div class="col-12">
              <label class="form-label">板块图标</label>
              <IconPicker v-model="form.icon" fallback="Database" />
            </div>
            <div class="col-md-6">
              <label class="option-card" :class="{ 'is-on': form.is_enabled }">
                <input v-model="form.is_enabled" class="form-check-input" type="checkbox" />
                <span>
                  <span class="option-card-title d-block">启用此板块</span>
                  <span class="option-card-desc d-block">禁用后不会出现在侧边栏导航中</span>
                </span>
              </label>
            </div>
            <div class="col-md-6">
              <label class="option-card" :class="{ 'is-on': form.auto_load_images }">
                <input v-model="form.auto_load_images" class="form-check-input" type="checkbox" />
                <span>
                  <span class="option-card-title d-block">图片{{ form.auto_load_images ? '自动加载' : '手动加载' }}</span>
                  <span class="option-card-desc d-block">关闭后列表中的图片需点击才加载，节省流量</span>
                </span>
              </label>
            </div>
            <div v-if="copySource && copySource.record_count > 0" class="col-12">
              <label class="option-card" :class="{ 'is-on': copySource.copyRecords }">
                <input v-model="copySource.copyRecords" class="form-check-input" type="checkbox" />
                <span>
                  <span class="option-card-title d-block">同时复制原板块中的现有记录数据（共 {{ copySource.record_count }} 条）</span>
                  <span class="option-card-desc d-block">
                    {{ copySource.copyRecords ? '新建后将一并克隆原板块内的全部记录数据' : '默认不勾选：仅复制板块结构与字段配置，创建全新的空数据板块' }}
                  </span>
                </span>
              </label>
            </div>
            <div class="col-12">
              <label class="form-label">板块说明</label>
              <textarea v-model="form.description" class="form-control" rows="2" placeholder="填写该板块的用途简述…"></textarea>
            </div>
          </div>
        </BaseTabPane>

        <BaseTabPane name="fields" label="字段配置" :badge="form.fields.length">
          <div class="add-field-bar">
            <select v-model="addingFieldId" class="form-select">
              <option :value="null">从字段库选择要添加的字段…（可选 {{ availableFields.length }} 个）</option>
              <option v-for="f in availableFields" :key="f.id" :value="f.id">
                {{ f.name }} ({{ f.code }}) - {{ typeLabel(f.type) }}
              </option>
            </select>
            <button class="btn btn-primary" :disabled="!addingFieldId" @click="addField">
              <Plus />添加
            </button>
            <template v-if="importableModules.length">
              <select v-model="importModuleId" class="form-select import-select">
                <option :value="null">从已有板块导入字段…</option>
                <option v-for="m in importableModules" :key="m.id" :value="m.id">
                  {{ m.name }} ({{ m.field_count }} 个字段)
                </option>
              </select>
              <button class="btn btn-outline-primary" :disabled="!importModuleId" @click="importFieldsFromModule">
                <Copy />导入字段
              </button>
            </template>
            <button class="btn btn-outline-secondary" @click="$router.push('/admin/fields')">
              <ExternalLink />管理字段库
            </button>
          </div>

          <div v-if="form.fields.length" class="field-table">
            <div class="field-row field-row-head">
              <span class="col-drag"></span>
              <span class="col-seq">#</span>
              <span class="col-name">字段</span>
              <span class="col-type">类型</span>
              <span class="col-check">必填</span>
              <span class="col-check">列表展示</span>
              <span class="col-width">列宽(px)</span>
              <span class="col-op"></span>
            </div>
            <draggable v-model="form.fields" item-key="field_id" handle=".drag-handle" class="field-list">
              <template #item="{ element, index }">
                <div class="field-row">
                  <span class="col-drag drag-handle" title="按住拖拽排序"><GripVertical /></span>
                  <span class="col-seq">{{ index + 1 }}</span>
                  <span class="col-name">
                    <span class="name-text">
                      <span class="name-title">{{ fieldOf(element.field_id)?.name }}</span>
                      <span class="name-sub">{{ fieldOf(element.field_id)?.code }}</span>
                    </span>
                  </span>
                  <span class="col-type">
                    <span class="badge text-bg-secondary">{{ typeLabel(fieldOf(element.field_id)?.type || '') }}</span>
                  </span>
                  <span class="col-check">
                    <input :id="`req${index}`" v-model="element.is_required" class="form-check-input" type="checkbox" title="必填" />
                  </span>
                  <span class="col-check">
                    <input :id="`sil${index}`" v-model="element.show_in_list" class="form-check-input" type="checkbox" title="列表展示" />
                  </span>
                  <span class="col-width">
                    <input v-model.number="element.column_width" type="number" min="60" max="600" class="form-control form-control-sm" placeholder="自动" />
                  </span>
                  <span class="col-op">
                    <button class="icon-button sm danger" type="button" v-tip="'移除字段'" @click="form.fields.splice(index, 1)">
                      <X />
                    </button>
                  </span>
                </div>
              </template>
            </draggable>
          </div>
          <div v-else class="empty-box">
            <ListPlus />
            <span>尚未添加任何字段，可从上方字段库选择，或直接从已有板块导入</span>
          </div>
          <small v-if="form.fields.length" class="form-hint mt-2">拖动左侧手柄调整字段顺序，顺序即表单与列表中的显示顺序。</small>
        </BaseTabPane>

        <BaseTabPane name="calculated" label="计算字段" :badge="form.calculated_fields.length || ''">
          <div class="callout mb-3">
            <Calculator />
            <span>剩余价值计算：根据「金额 × 剩余天数 / 总天数」自动得出，可选字段来自本板块已添加的数值与日期字段。</span>
          </div>
          <div v-for="(calc, index) in form.calculated_fields" :key="index" class="calc-card">
            <div class="calc-card-head">
              <span class="calc-card-title"><Calculator />计算字段 {{ index + 1 }}</span>
              <button class="icon-button sm danger" type="button" v-tip="'删除此计算字段'" @click="form.calculated_fields.splice(index, 1)">
                <Trash2 />
              </button>
            </div>
            <div class="row g-2">
              <div class="col-md-3">
                <label class="form-label">显示名称</label>
                <input v-model="calc.name" class="form-control form-control-sm" placeholder="显示名称" />
              </div>
              <div class="col-md-3">
                <label class="form-label">字段编码</label>
                <input v-model="calc.code" class="form-control form-control-sm" placeholder="字段编码" />
              </div>
              <div class="col-md-2">
                <label class="form-label">小数精度</label>
                <input v-model.number="calc.precision" type="number" min="0" max="6" class="form-control form-control-sm" placeholder="精度" />
              </div>
              <div class="col-md-4 d-flex align-items-end gap-3 pb-1">
                <div class="form-check mb-0">
                  <input :id="`csil${index}`" v-model="calc.show_in_list" class="form-check-input" type="checkbox" />
                  <label :for="`csil${index}`" class="form-check-label">列表展示</label>
                </div>
                <div class="form-check mb-0">
                  <input :id="`csum${index}`" v-model="calc.enable_summary" class="form-check-input" type="checkbox" />
                  <label :for="`csum${index}`" class="form-check-label">合计统计</label>
                </div>
              </div>
              <div class="col-md-4">
                <label class="form-label">金额字段</label>
                <select v-model="calc.amount_field" class="form-select form-select-sm">
                  <option value="">请选择金额字段</option>
                  <option v-for="f in numberFields" :key="f.code" :value="f.code">{{ f.name }} ({{ f.code }})</option>
                </select>
              </div>
              <div class="col-md-4">
                <label class="form-label">开始时间</label>
                <select v-model="calc.start_field" class="form-select form-select-sm">
                  <option value="">请选择开始时间</option>
                  <option v-for="f in dateFields" :key="f.code" :value="f.code">{{ f.name }} ({{ f.code }})</option>
                </select>
              </div>
              <div class="col-md-4">
                <label class="form-label">结束时间</label>
                <select v-model="calc.end_field" class="form-select form-select-sm">
                  <option value="">请选择结束时间</option>
                  <option v-for="f in dateFields" :key="f.code" :value="f.code">{{ f.name }} ({{ f.code }})</option>
                </select>
              </div>
            </div>
          </div>
          <div v-if="!form.calculated_fields.length" class="empty-box">
            <Calculator />
            <span>尚未配置计算字段</span>
          </div>
          <button class="btn btn-outline-primary btn-sm mt-3" type="button" @click="addCalculatedField">
            <Plus />添加剩余价值计算
          </button>
        </BaseTabPane>
      </BaseTab>

      <template #footer>
        <span class="me-auto toolbar-meta d-none d-md-inline">
          已选 <strong>{{ form.fields.length }}</strong> 个字段 · <strong>{{ form.calculated_fields.length }}</strong> 个计算字段
        </span>
        <button class="btn btn-outline-secondary" @click="dialog = false">取消</button>
        <button class="btn btn-primary" :disabled="saving" @click="save">
          <span v-if="saving" class="spinner-border spinner-border-sm"></span>{{ copySource ? '创建复制板块' : '保存板块' }}
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import draggable from 'vuedraggable'
import {
  Calculator,
  Copy,
  ExternalLink,
  GripVertical,
  LayoutGrid,
  ListPlus,
  Plus,
  Search,
  SquarePen,
  Trash2,
  X,
} from 'lucide-vue-next'
import {
  categoryApi, fieldApi, moduleApi,
  type CategoryOut, type FieldDef, type FieldType, type ModuleListItem,
} from '@/api'
import { useNavStore } from '@/stores/nav'
import { toast, confirm } from '@/utils/ui'
import { vLoading } from '@/components/ui/loading'
import { vTip } from '@/components/ui/tooltip'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseTab from '@/components/ui/BaseTab.vue'
import BaseTabPane from '@/components/ui/BaseTabPane.vue'
import SkeletonTable from '@/components/ui/SkeletonTable.vue'
import IconPicker from '@/components/ui/IconPicker.vue'
import { RouterLink } from 'vue-router'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppIcon from '@/components/AppIcon.vue'

const list = ref<ModuleListItem[]>([])
const categories = ref<CategoryOut[]>([])
const fields = ref<FieldDef[]>([])
const types = ref<FieldType[]>([])
const loading = ref(false)
const firstLoad = ref(true)
const dialog = ref(false)
const saving = ref(false)
const tab = ref('base')
const addingFieldId = ref<number | null>(null)
const importModuleId = ref<number | null>(null)
const keyword = ref('')
const nav = useNavStore()

const copySource = ref<{
  id: number
  name: string
  code: string
  record_count: number
  copyRecords: boolean
} | null>(null)

const form = reactive<any>({
  id: null,
  code: '', name: '', icon: null, description: '',
  sort_order: 0, is_enabled: true, auto_load_images: true, category_id: null,
  fields: [] as { field_id: number; sort_order: number; is_required: boolean; show_in_list: boolean; column_width: number | null }[],
  calculated_fields: [] as any[],
})

const modalTitle = computed(() => {
  if (form.id) return `编辑板块 · ${form.name || form.code}`
  if (copySource.value) return `复制新建板块 · 来源：${copySource.value.name}`
  return '新建板块'
})

const filteredList = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return list.value
  return list.value.filter(
    (m) =>
      m.name.toLowerCase().includes(kw) ||
      m.code.toLowerCase().includes(kw) ||
      categoryName(m.category_id).toLowerCase().includes(kw)
  )
})

const availableFields = computed(() =>
  fields.value.filter((f) => !form.fields.find((x: any) => x.field_id === f.id))
)

const importableModules = computed(() =>
  list.value.filter((m) => m.id !== form.id && m.field_count > 0)
)

const moduleSelectedFields = computed(() =>
  form.fields.map((item: any) => fieldOf(item.field_id)).filter(Boolean) as FieldDef[]
)

const numberFields = computed(() => moduleSelectedFields.value.filter((f) => f.type === 'number'))
const dateFields = computed(() => moduleSelectedFields.value.filter((f) => ['date', 'datetime'].includes(f.type)))

function fieldOf(id: number) {
  return fields.value.find((f) => f.id === id)
}
function typeLabel(t: string) {
  return types.value.find((x) => x.type === t)?.label || t
}
function categoryName(id?: number | null) {
  return categories.value.find((c) => c.id === id)?.name || '-'
}

function suggestCopyCode(baseCode: string) {
  const existing = new Set(list.value.map((m) => m.code.toLowerCase()))
  const cleanBase = baseCode.replace(/_copy(_\d+)?$/i, '').slice(0, 50) || 'module'
  let candidate = `${cleanBase}_copy`
  let seq = 2
  while (existing.has(candidate.toLowerCase())) {
    candidate = `${cleanBase}_copy_${seq}`
    seq++
  }
  return candidate
}

async function load() {
  loading.value = true
  try {
    const [m, c, f, t] = await Promise.all([
      moduleApi.list(),
      categoryApi.list(),
      fieldApi.list(),
      fieldApi.types(),
    ])
    list.value = m.data
    categories.value = c.data
    fields.value = f.data
    types.value = t.data
  } finally {
    loading.value = false
    firstLoad.value = false
  }
}

async function openDialog(row?: ModuleListItem) {
  tab.value = 'base'
  copySource.value = null
  importModuleId.value = null
  if (row) {
    const { data: full } = await moduleApi.get(row.id)
    Object.assign(form, {
      id: full.id,
      code: full.code, name: full.name, icon: full.icon, description: full.description || '',
      sort_order: full.sort_order, is_enabled: full.is_enabled, auto_load_images: full.auto_load_images, category_id: full.category_id,
      fields: full.fields.map((mf) => ({
        field_id: mf.field_id,
        sort_order: mf.sort_order,
        is_required: mf.is_required,
        show_in_list: mf.show_in_list,
        column_width: mf.column_width || null,
      })),
      calculated_fields: (full.calculated_fields || []).map((item) => ({ ...item })),
    })
  } else {
    Object.assign(form, {
      id: null, code: '', name: '', icon: null, description: '',
      sort_order: 0, is_enabled: true, auto_load_images: true, category_id: null, fields: [], calculated_fields: [],
    })
  }
  dialog.value = true
}

async function duplicateModule(row: ModuleListItem) {
  tab.value = 'base'
  importModuleId.value = null
  const { data: full } = await moduleApi.get(row.id)
  copySource.value = {
    id: full.id,
    name: full.name,
    code: full.code,
    record_count: row.record_count,
    copyRecords: false,
  }
  Object.assign(form, {
    id: null,
    code: suggestCopyCode(full.code),
    name: `${full.name}_副本`,
    icon: full.icon,
    description: full.description || '',
    sort_order: full.sort_order,
    is_enabled: full.is_enabled,
    auto_load_images: full.auto_load_images,
    category_id: full.category_id,
    fields: full.fields.map((mf) => ({
      field_id: mf.field_id,
      sort_order: mf.sort_order,
      is_required: mf.is_required,
      show_in_list: mf.show_in_list,
      column_width: mf.column_width || null,
    })),
    calculated_fields: (full.calculated_fields || []).map((item) => ({ ...item })),
  })
  dialog.value = true
}

async function importFieldsFromModule() {
  if (!importModuleId.value) return
  const { data: src } = await moduleApi.get(importModuleId.value)
  let added = 0
  for (const mf of src.fields) {
    if (!form.fields.some((x: any) => x.field_id === mf.field_id)) {
      form.fields.push({
        field_id: mf.field_id,
        sort_order: form.fields.length + 1,
        is_required: mf.is_required,
        show_in_list: mf.show_in_list,
        column_width: mf.column_width || null,
      })
      added++
    }
  }
  let addedCalc = 0
  for (const cf of src.calculated_fields || []) {
    if (!form.calculated_fields.some((x: any) => x.code === cf.code)) {
      form.calculated_fields.push({ ...cf })
      addedCalc++
    }
  }
  importModuleId.value = null
  toast(
    added || addedCalc
      ? `已从「${src.name}」导入 ${added} 个字段${addedCalc ? `、${addedCalc} 个计算字段` : ''}`
      : `「${src.name}」中的字段均已在列表中`,
    'success'
  )
}

function addField() {
  if (!addingFieldId.value) return
  form.fields.push({
    field_id: addingFieldId.value,
    sort_order: form.fields.length + 1,
    is_required: false,
    show_in_list: true,
    column_width: 140,
  })
  addingFieldId.value = null
}

function addCalculatedField() {
  form.calculated_fields.push({
    name: '剩余价值',
    code: `calc_remain_${form.calculated_fields.length + 1}`,
    type: 'remaining_value_by_date',
    amount_field: '',
    start_field: '',
    end_field: '',
    precision: 2,
    enable_summary: true,
    show_in_list: true,
    sort_order: 99,
  })
}

async function save() {
  if (!form.code || !form.name) {
    toast('请填写板块编码与名称', 'warning')
    tab.value = 'base'
    return
  }
  saving.value = true
  try {
    const payload: any = {
      ...form,
      fields: form.fields.map((f: any, idx: number) => ({ ...f, sort_order: idx + 1 })),
    }
    if (!form.id && copySource.value?.copyRecords) {
      payload.copy_records_from_id = copySource.value.id
    }
    if (form.id) {
      await moduleApi.update(form.id, payload)
      toast('板块配置已保存', 'success')
    } else {
      await moduleApi.create(payload)
      toast(copySource.value ? '已复制创建新板块' : '板块已创建', 'success')
    }
    dialog.value = false
    copySource.value = null
    await load()
    await nav.refresh()
  } finally {
    saving.value = false
  }
}

async function remove(row: ModuleListItem) {
  if (!(await confirm(`确定删除板块「${row.name}」？所有数据将无法直接访问`, { danger: true }))) return
  await moduleApi.remove(row.id)
  toast('板块已删除', 'success')
  await load()
  await nav.refresh()
}

onMounted(load)
</script>

<style scoped>
.row-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.add-field-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.add-field-bar .form-select {
  flex: 1 1 260px;
  max-width: 420px;
}

.add-field-bar .import-select {
  flex: 0 1 220px;
  max-width: 240px;
}

/* ---------- 字段配置列表 ---------- */
.field-table {
  overflow: hidden;
  border: 1px solid var(--hairline);
  border-radius: var(--radius);
}

.field-list {
  display: flex;
  flex-direction: column;
}

.field-row {
  display: grid;
  grid-template-columns: 28px 28px minmax(160px, 1fr) 110px 64px 76px 100px 40px;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-elev);
}

.field-list .field-row + .field-row {
  border-top: 1px solid var(--border-faint);
}

.field-list .field-row:hover {
  background: var(--bg-hover);
}

.field-row-head {
  border-bottom: 1px solid var(--hairline);
  background: var(--bg-table-head);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
}

.col-check {
  display: flex;
  justify-content: center;
}

.col-check .form-check-input {
  margin: 0;
}

.col-seq {
  color: var(--text-faint);
  font-family: var(--font-mono);
  font-size: 11px;
}

.col-name {
  min-width: 0;
}

.col-op {
  display: flex;
  justify-content: flex-end;
}

.drag-handle {
  display: grid;
  place-items: center;
  color: var(--text-faint);
  cursor: grab;
  user-select: none;
}

.drag-handle:hover {
  color: var(--text);
}

.drag-handle .lucide {
  width: 16px;
  height: 16px;
}

.sortable-ghost {
  opacity: 0.5;
  background: var(--accent-soft) !important;
}

@media (max-width: 767.98px) {
  .field-row {
    grid-template-columns: 24px 22px minmax(120px, 1fr) 54px 64px 40px;
  }

  .field-row .col-type,
  .field-row .col-width {
    display: none;
  }
}

/* ---------- 计算字段 ---------- */
.calc-card {
  padding: 14px 16px 16px;
  border: 1px solid var(--hairline);
  border-radius: var(--radius);
  background: var(--bg-elev);
}

.calc-card + .calc-card {
  margin-top: 10px;
}

.calc-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.calc-card-title {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--text);
  font-size: 12px;
  font-weight: 600;
}

.calc-card-title .lucide {
  width: 15px;
  height: 15px;
  color: var(--info);
}

.calc-card .form-label {
  margin-bottom: 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-muted);
}

.empty-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px 16px;
  border: 1px dashed var(--hairline-strong);
  border-radius: var(--radius);
  background: var(--bg-soft);
  color: var(--text-muted);
  font-size: 12px;
}

.empty-box .lucide {
  width: 22px;
  height: 22px;
  color: var(--text-faint);
}
</style>
