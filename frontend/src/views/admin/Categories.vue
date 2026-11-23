<template>
  <div class="page">
    <PageHeader title="分类管理" eyebrow="结构配置" subtitle="管理业务板块的一级导航分类与显示顺序，数字越小在导航中越靠前">
      <template #links>
        <RouterLink to="/admin/fields"><List />2. 字段管理</RouterLink>
        <RouterLink to="/admin/modules"><LayoutGrid />3. 板块管理</RouterLink>
      </template>
    </PageHeader>

    <div class="ovh-toolbar">
      <div class="toolbar-group">
        <button class="btn btn-primary" @click="openDialog()">
          <Plus />新建分类
        </button>
        <span class="toolbar-meta ms-1">共 <strong>{{ list.length }}</strong> 个分类</span>
      </div>
      <div class="toolbar-group">
        <div class="search-box">
          <Search />
          <input v-model="keyword" class="form-control" placeholder="按分类名称搜索…" />
          <button v-if="keyword" class="search-box-clear" type="button" aria-label="清除" @click="keyword = ''">
            <X />
          </button>
        </div>
      </div>
    </div>

    <div class="ovh-table-wrap">
      <SkeletonTable v-if="loading && firstLoad" :rows="6" :cols="5" />
      <div v-else class="table-responsive" v-loading="loading && !firstLoad">
        <table class="table table-hover align-middle">
          <thead>
            <tr>
              <th style="width: 64px" class="text-center">#</th>
              <th>分类名称</th>
              <th class="text-end" style="width: 110px">显示排序</th>
              <th style="width: 140px">关联板块</th>
              <th style="width: 180px">创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in filteredList" :key="row.id" @dblclick="openDialog(row)">
              <td class="cell-mono cell-faint text-center">{{ i + 1 }}</td>
              <td>
                <span class="name-cell">
                  <span class="name-ico"><AppIcon :name="row.icon" fallback="Folder" /></span>
                  <span class="name-title">{{ row.name }}</span>
                </span>
              </td>
              <td class="text-end cell-mono">{{ row.sort_order }}</td>
              <td>
                <span class="badge" :class="row.module_count ? 'badge-purple' : 'text-bg-secondary'">
                  {{ row.module_count }} 个板块
                </span>
              </td>
              <td class="cell-mono cell-muted cell-last">
                <span>{{ formatTime(row.created_at) }}</span>
                <div class="row-float-actions" @dblclick.stop>
                  <button class="icon-button sm primary" v-tip="'编辑分类 (或双击行)'" @click="openDialog(row)">
                    <SquarePen />
                  </button>
                  <button class="icon-button sm danger" v-tip="'删除分类'" @click="remove(row)">
                    <Trash2 />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="!loading && !filteredList.length" class="empty-state">
          <FolderOpen />
          <template v-if="list.length">
            <div class="empty-state-title">没有匹配的分类</div>
          </template>
          <template v-else>
            <div class="empty-state-title">暂无业务分类</div>
            <p>创建第一个分类，用于在侧边栏中对板块进行分组。</p>
            <button class="btn btn-primary btn-sm" @click="openDialog()"><Plus />新建分类</button>
          </template>
        </div>
      </div>
    </div>

    <BaseModal v-model="dialog" :title="form.id ? '编辑分类' : '新建分类'" :close-on-backdrop="false">
      <div class="mb-3">
        <label class="form-label">分类名称 <span class="text-danger">*</span></label>
        <input v-model="form.name" class="form-control" placeholder="如：资产管理、日常账号…" @keyup.enter="save" />
      </div>
      <div class="mb-3">
        <label class="form-label">分类图标</label>
        <IconPicker v-model="form.icon" fallback="Folder" />
      </div>
      <div>
        <label class="form-label">显示排序</label>
        <input v-model.number="form.sort_order" type="number" min="0" class="form-control" style="max-width: 160px" />
        <small class="form-hint">数字越小，在侧边栏中显示越靠前</small>
      </div>
      <template #footer>
        <button class="btn btn-outline-secondary" @click="dialog = false">取消</button>
        <button class="btn btn-primary" :disabled="saving" @click="save">
          <span v-if="saving" class="spinner-border spinner-border-sm"></span>保存分类
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { FolderOpen, LayoutGrid, List, Plus, Search, SquarePen, Trash2, X } from 'lucide-vue-next'
import { categoryApi, type CategoryOut } from '@/api'
import { useNavStore } from '@/stores/nav'
import { toast, confirm } from '@/utils/ui'
import { vLoading } from '@/components/ui/loading'
import { vTip } from '@/components/ui/tooltip'
import BaseModal from '@/components/ui/BaseModal.vue'
import SkeletonTable from '@/components/ui/SkeletonTable.vue'
import IconPicker from '@/components/ui/IconPicker.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppIcon from '@/components/AppIcon.vue'

const list = ref<CategoryOut[]>([])
const loading = ref(false)
const firstLoad = ref(true)
const dialog = ref(false)
const saving = ref(false)
const keyword = ref('')
const nav = useNavStore()

const form = reactive<{ id?: number; name: string; icon: string | null; sort_order: number }>({
  name: '',
  icon: null,
  sort_order: 0,
})

const filteredList = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return list.value
  return list.value.filter((c) => c.name.toLowerCase().includes(kw))
})

async function load() {
  loading.value = true
  try {
    const { data } = await categoryApi.list()
    list.value = data
  } finally {
    loading.value = false
    firstLoad.value = false
  }
}

function openDialog(row?: CategoryOut) {
  if (row) {
    form.id = row.id
    form.name = row.name
    form.icon = row.icon ?? null
    form.sort_order = row.sort_order
  } else {
    form.id = undefined
    form.name = ''
    form.icon = null
    form.sort_order = 0
  }
  dialog.value = true
}

async function save() {
  if (!form.name.trim()) {
    toast('请输入分类名称', 'warning')
    return
  }
  saving.value = true
  try {
    if (form.id) {
      await categoryApi.update(form.id, { name: form.name, icon: form.icon, sort_order: form.sort_order })
    } else {
      await categoryApi.create({ name: form.name, icon: form.icon, sort_order: form.sort_order })
    }
    toast('分类保存成功', 'success')
    dialog.value = false
    await load()
    await nav.refresh()
  } finally {
    saving.value = false
  }
}

async function remove(row: CategoryOut) {
  if (!(await confirm(`确认删除分类「${row.name}」？若分类下有板块，其分类将被置为空。`, { danger: true }))) return
  await categoryApi.remove(row.id)
  toast('分类已删除', 'success')
  await load()
  await nav.refresh()
}

function formatTime(s: string) {
  return s ? new Date(s).toLocaleString('zh-CN') : ''
}

onMounted(load)
</script>
