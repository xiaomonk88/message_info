<template>
  <!-- 文本 / URL / Email -->
  <input
    v-if="['text', 'url', 'email'].includes(field.type)"
    class="form-control"
    :type="field.type === 'email' ? 'email' : field.type === 'url' ? 'url' : 'text'"
    :value="modelValue ?? ''"
    :placeholder="opts.placeholder"
    :maxlength="opts.maxLength || undefined"
    :disabled="disabled"
    @input="emitVal(($event.target as HTMLInputElement).value)"
  />

  <!-- 密码 -->
  <div v-else-if="field.type === 'password'" class="input-group">
    <input
      class="form-control"
      :type="showPwd ? 'text' : 'password'"
      :value="modelValue ?? ''"
      :placeholder="opts.placeholder"
      :disabled="disabled"
      @input="emitVal(($event.target as HTMLInputElement).value)"
    />
    <button type="button" class="btn btn-outline-secondary" :disabled="disabled" @click="showPwd = !showPwd">
      <EyeOff v-if="showPwd" /><Eye v-else />
    </button>
  </div>

  <!-- 多行文本 / JSON -->
  <textarea
    v-else-if="field.type === 'textarea' || field.type === 'json'"
    class="form-control"
    :rows="field.type === 'json' ? 6 : opts.rows || 4"
    :value="modelValue ?? ''"
    :placeholder="field.type === 'json' ? '请输入合法的 JSON' : opts.placeholder"
    :maxlength="field.type === 'textarea' ? opts.maxLength || undefined : undefined"
    :disabled="disabled"
    @input="emitVal(($event.target as HTMLTextAreaElement).value)"
  ></textarea>

  <!-- 数字 -->
  <input
    v-else-if="field.type === 'number'"
    class="form-control"
    type="number"
    :value="modelValue ?? ''"
    :min="opts.min"
    :max="opts.max"
    :step="numberStep"
    :placeholder="opts.placeholder"
    :disabled="disabled"
    @input="emitNumber(($event.target as HTMLInputElement).value)"
  />

  <!-- 布尔 -->
  <div v-else-if="field.type === 'boolean'" class="form-check form-switch">
    <input
      class="form-check-input"
      type="checkbox"
      role="switch"
      :checked="!!modelValue"
      :disabled="disabled"
      @change="emitVal(($event.target as HTMLInputElement).checked)"
    />
  </div>

  <!-- 日期 -->
  <input
    v-else-if="field.type === 'date'"
    class="form-control"
    type="date"
    :value="modelValue ?? ''"
    :disabled="disabled"
    @input="emitVal(($event.target as HTMLInputElement).value || null)"
  />

  <!-- 日期时间 -->
  <input
    v-else-if="field.type === 'datetime'"
    class="form-control"
    type="datetime-local"
    step="1"
    :value="toLocalInput(modelValue)"
    :disabled="disabled"
    @input="emitDatetime(($event.target as HTMLInputElement).value)"
  />

  <!-- 单选 -->
  <select
    v-else-if="field.type === 'select'"
    class="form-select"
    :value="modelValue ?? ''"
    :disabled="disabled"
    @change="emitVal(($event.target as HTMLSelectElement).value || null)"
  >
    <option value="">{{ opts.placeholder || '请选择' }}</option>
    <option v-for="c in choices" :key="choiceVal(c)" :value="choiceVal(c)">{{ choiceLabel(c) }}</option>
  </select>

  <!-- 多选 -->
  <select
    v-else-if="field.type === 'multiselect'"
    class="form-select"
    multiple
    :size="Math.min(choices.length || 3, 6)"
    :disabled="disabled"
    @change="emitMultiselect($event)"
  >
    <option
      v-for="c in choices"
      :key="choiceVal(c)"
      :value="choiceVal(c)"
      :selected="Array.isArray(modelValue) && modelValue.includes(choiceVal(c))"
    >
      {{ choiceLabel(c) }}
    </option>
  </select>

  <!-- 图片 / 文件 -->
  <div v-else-if="field.type === 'image' || field.type === 'file'" class="upload-field">
    <!-- 图片预览 -->
    <div v-if="modelValue && isImage" class="upload-preview">
      <span v-if="loadFailed" class="upload-missing" :title="String(modelValue)">图片路径失效</span>
      <button v-else type="button" class="upload-thumb" title="预览图片" @click="previewVisible = true">
        <img v-if="displayUrl" :src="displayUrl" alt="图片预览" @error="loadFailed = true" />
      </button>
      <div class="btn-group btn-group-sm">
        <button type="button" class="btn btn-outline-secondary" :disabled="loadFailed" @click="previewVisible = true">
          <Eye class="me-1" />预览
        </button>
        <button type="button" class="btn btn-outline-secondary" :disabled="loadFailed" @click="download">
          <Download class="me-1" />下载
        </button>
      </div>
    </div>

    <!-- 文件链接 -->
    <button v-if="modelValue && !isImage" type="button" class="btn btn-link p-0" @click="download">
      <Paperclip class="me-1" />{{ filename }}
    </button>

    <div class="d-flex align-items-center gap-2">
      <input ref="fileInput" type="file" class="d-none" :accept="accept" @change="onFileChange" />
      <button type="button" class="btn btn-sm btn-outline-primary" :disabled="disabled || uploading" @click="fileInput?.click()">
        <span v-if="uploading" class="spinner-border spinner-border-sm me-1"></span>
        <Upload v-else class="me-1" />{{ modelValue ? '更换' : '上传' }}
      </button>
      <button v-if="modelValue" type="button" class="btn btn-sm btn-link text-danger p-0" :disabled="disabled" @click="emitVal(null)">
        清除
      </button>
    </div>

    <BaseModal v-model="previewVisible" title="图片预览" size="lg">
      <div class="upload-dialog-body">
        <img v-if="displayUrl" :src="displayUrl" alt="图片预览" />
      </div>
      <template #footer>
        <button class="btn btn-outline-secondary" @click="previewVisible = false">关闭</button>
        <button class="btn btn-primary" @click="download"><Download class="me-1" />下载</button>
      </template>
    </BaseModal>
  </div>

  <!-- 兜底 -->
  <input
    v-else
    class="form-control"
    :value="modelValue ?? ''"
    :disabled="disabled"
    @input="emitVal(($event.target as HTMLInputElement).value)"
  />
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Download, Eye, EyeOff, Paperclip, Upload } from 'lucide-vue-next'
import { uploadApi, type FieldDef } from '@/api'
import {
  downloadProtectedFile,
  fetchProtectedBlob,
  fileNameFromPath,
  resolveFileUrl,
} from '@/utils/files'
import { toast } from '@/utils/ui'
import BaseModal from '@/components/ui/BaseModal.vue'

const props = defineProps<{
  field: FieldDef
  modelValue: any
  disabled?: boolean
}>()

const emit = defineEmits<{ (e: 'update:modelValue', v: any): void }>()

const opts = computed<any>(() => props.field.options || {})
const showPwd = ref(false)

function emitVal(v: any) {
  emit('update:modelValue', v)
}

function emitNumber(raw: string) {
  if (raw === '') return emitVal(null)
  emit('update:modelValue', Number(raw))
}

const numberStep = computed(() => {
  const p = opts.value.precision
  if (!p || p <= 0) return 1
  return Number(`0.${'0'.repeat(p - 1)}1`)
})

/* ---------- 选项 ---------- */
const choices = computed<any[]>(() => opts.value.choices || [])
function choiceVal(c: any) {
  return typeof c === 'object' ? c.value : c
}
function choiceLabel(c: any) {
  return typeof c === 'object' ? c.label || c.value : c
}
function emitMultiselect(e: Event) {
  const selected = Array.from((e.target as HTMLSelectElement).selectedOptions).map((o) => o.value)
  emit('update:modelValue', selected)
}

/* ---------- 日期时间 ↔ 输入框 ---------- */
function toLocalInput(v: any): string {
  if (!v) return ''
  // 存储格式 'YYYY-MM-DD HH:mm:ss' → 输入框 'YYYY-MM-DDTHH:mm:ss'
  return String(v).replace(' ', 'T')
}
function emitDatetime(raw: string) {
  if (!raw) return emitVal(null)
  // 'YYYY-MM-DDTHH:mm[:ss]' → 'YYYY-MM-DD HH:mm:ss'
  let s = raw.replace('T', ' ')
  if (s.length === 16) s += ':00'
  emit('update:modelValue', s)
}

/* ---------- 上传（图片/文件） ---------- */
const isImage = computed(() => props.field.type === 'image')
const accept = computed(() => (isImage.value ? 'image/*' : '*'))
const maxSize = computed<number>(() => (opts.value.maxSize as number) || (isImage.value ? 5 : 50))
const fileInput = ref<HTMLInputElement>()
const uploading = ref(false)
const previewVisible = ref(false)
const objectUrl = ref('')
const loadFailed = ref(false)

const fileUrl = computed(() => resolveFileUrl(props.modelValue))
// 受保护的 /api 图片只用带 token 拉取后的 blob 地址，避免 <img> 裸请求导致 401
const displayUrl = computed(() => objectUrl.value || (fileUrl.value.startsWith('/api/') ? '' : fileUrl.value))
const filename = computed(() => fileNameFromPath(props.modelValue, props.field.code))

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = '' // 允许重复选择同一文件
  if (!file) return
  if (file.size > maxSize.value * 1024 * 1024) {
    toast(`文件大小不能超过 ${maxSize.value}MB`, 'error')
    return
  }
  uploading.value = true
  try {
    const { data } = await uploadApi.upload(file)
    emit('update:modelValue', data.path)
    toast('上传成功', 'success')
  } catch {
    toast('上传失败', 'error')
  } finally {
    uploading.value = false
  }
}

async function download() {
  if (!fileUrl.value) return
  try {
    await downloadProtectedFile(fileUrl.value, filename.value)
  } catch {
    toast('文件下载失败', 'error')
  }
}

watch(
  fileUrl,
  async (url) => {
    if (objectUrl.value) {
      URL.revokeObjectURL(objectUrl.value)
      objectUrl.value = ''
    }
    loadFailed.value = false
    if (!isImage.value || !url || !url.startsWith('/api/')) return
    try {
      const blob = await fetchProtectedBlob(url)
      objectUrl.value = URL.createObjectURL(blob)
    } catch {
      loadFailed.value = true
    }
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  if (objectUrl.value) URL.revokeObjectURL(objectUrl.value)
})
</script>

<style scoped>
.upload-field {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.upload-preview {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
}

.upload-thumb {
  width: 88px;
  height: 64px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-elev);
  padding: 2px;
  transition: border-color 0.15s ease;
}

.upload-thumb:hover {
  border-color: var(--accent);
}

.upload-thumb img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  border-radius: 2px;
}

.upload-missing {
  display: inline-flex;
  height: 28px;
  align-items: center;
  border: 1px solid rgba(220, 38, 38, 0.3);
  border-radius: var(--radius-sm);
  color: var(--danger);
  background: var(--danger-soft);
  padding: 0 10px;
  font-size: 11px;
}

.upload-dialog-body {
  width: 100%;
  height: min(62vh, 560px);
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
}

.upload-dialog-body img {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
}
</style>
