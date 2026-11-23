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
      <SkeletonTable v-if="loading && firstLoad" :rows="8" :cols="7" />
      <div v-else class="table-responsive" v-loading="loading && !firstLoad">
        <table class="table table-hover align-middle">
          <thead>
            <tr>
              <th style="width: 240px">板块</th>
              <th style="width: 120px">分类</th>
              <th class="text-end" style="width: 70px">字段</th>
              <th class="text-end" style="width: 84px">记录</th>
              <th class="text-end" style="width: 68px">排序</th>
              <th style="width: 84px">状态</th>
              <th style="width: 84px">图片</th>
              <th>说明</th>
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
              <td class="text-end cell-mono fw-semibold text-primary">{{ row.record_count }}</td>
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
              <td class="text-truncate cell-muted cell-last" style="max-width: 260px" :title="row.description || ''">
                <span>{{ row.description || '—' }}</span>
                <div class="row-float-actions" @dblclick.stop>
                  <button class="icon-button sm" v-tip="'查看记录'" @click="$router.push(`/m/${row.id}`)">
                    <ExternalLink />
                  </button>
                  <button class="icon-button sm primary" v-tip="'编辑配置 (或双击行)'" @click="openDialog(row)">
                    <SquarePen />
                  </button>
                  <button class="icon-button sm danger" v-tip="'删除板块'" @click="remove(row)">
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

    <!-- 新建 / 编辑板块 -->
    <BaseModal v-model="dialog" :title="form.id ? `编辑板块 · ${form.name || form.code}` : '新建板块'" size="xl" :close-on-backdrop="false">
      <BaseTab v-model="tab">
        <BaseTabPane name="base" label="基础信息">
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label">编码 <span class="text-danger">*</span></label>
              <input v-model="form.code" class="form-control" :disabled="!!form.id" placeholder="英文/数字/下划线，如 server_list" />
              <small v-if="form.id" class="form-hint">编码创建后不可修改</small>
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
            <span>尚未添加任何字段，请从上方字段库中选择</span>
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
          <span v-if="saving" class="spinner-border spinner-border-sm"></span>保存板块
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
const keyword = ref('')
const nav = useNavStore()

const form = reactive<any>({
  id: null,
  code: '', name: '', icon: null, description: '',
  sort_order: 0, is_enabled: true, auto_load_images: true, category_id: null,
  fields: [] as { field_id: number; sort_order: number; is_required: boolean; show_in_list: boolean; column_width: number | null }[],
  calculated_fields: [] as any[],
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
    formula_type: 'linear_depreciation',
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
    const payload = {
      ...form,
      fields: form.fields.map((f: any, idx: number) => ({ ...f, sort_order: idx + 1 })),
    }
    if (form.id) {
      await moduleApi.update(form.id, payload)
    } else {
      await moduleApi.create(payload)
    }
    toast('板块配置已保存', 'success')
    dialog.value = false
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
.add-field-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.add-field-bar .form-select {
  flex: 1 1 320px;
  max-width: 480px;
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
