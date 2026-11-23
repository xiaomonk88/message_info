<template>
  <template v-if="field.type === 'image'">
    <span v-if="!imageUrl" class="empty-value">-</span>
    <button
      v-else-if="!shouldDisplayImage && !imageFailed"
      class="image-lazy"
      type="button"
      title="点击加载图片"
      @click="loadAndPreview"
    >
      点击加载
    </button>
    <span v-else-if="imageFailed" class="image-missing" :title="String(value)">图片失效</span>
    <span v-else-if="!displayImageUrl" class="image-loading" title="加载中…"></span>
    <button v-else class="image-trigger" type="button" title="预览图片" @click="previewVisible = true">
      <img :src="displayImageUrl" alt="图片预览" @error="imageFailed = true" />
    </button>

    <BaseModal v-model="previewVisible" title="图片预览" size="lg">
      <div class="preview-body">
        <img v-if="displayImageUrl" :src="displayImageUrl" alt="图片预览" />
      </div>
      <template #footer>
        <button class="btn btn-outline-secondary" @click="previewVisible = false">关闭</button>
        <button class="btn btn-primary" @click="downloadImage"><Download class="me-1" />下载</button>
      </template>
    </BaseModal>
  </template>
  <span v-else-if="field.type === 'boolean'">
    <span class="badge" :class="value ? 'text-bg-success' : 'text-bg-secondary'">{{ value ? '是' : '否' }}</span>
  </span>
  <span v-else :title="metaTitle">{{ display }}</span>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Download } from 'lucide-vue-next'
import type { FieldDef } from '@/api'
import {
  downloadProtectedFile,
  fetchProtectedBlob,
  fileNameFromPath,
  resolveFileUrl,
} from '@/utils/files'
import { toast } from '@/utils/ui'
import BaseModal from '@/components/ui/BaseModal.vue'

const props = withDefaults(defineProps<{ field: FieldDef; value: any; meta?: any; autoLoadImage?: boolean }>(), {
  autoLoadImage: true,
})

const previewVisible = ref(false)
const objectUrl = ref('')
const imageFailed = ref(false)
const manualLoaded = ref(false)

// 只有图片类型字段才当作文件路径处理；否则每个文本单元格都会去请求 /api/v1/files/<文本>
const isImageField = computed(() => props.field.type === 'image')
const imageUrl = computed(() => (isImageField.value ? resolveFileUrl(props.value) : ''))
const isProtected = computed(() => imageUrl.value.startsWith('/api/'))
const shouldDisplayImage = computed(() => props.autoLoadImage || manualLoaded.value)
// 受保护的 /api 图片只用带 token 拉取后的 blob 地址；外链图片直接使用
const displayImageUrl = computed(() => objectUrl.value || (isProtected.value ? '' : imageUrl.value))
const filename = computed(() => fileNameFromPath(props.value, `${props.field.code}.jpg`))

const display = computed(() => {
  const v = props.value
  if (v === null || v === undefined || v === '') return '-'
  switch (props.field.type) {
    case 'multiselect':
      return Array.isArray(v) ? v.join(', ') : String(v)
    case 'json':
      return typeof v === 'string' ? v : JSON.stringify(v)
    default:
      return String(v)
  }
})

const metaTitle = computed(() => {
  const meta = props.meta
  if (!meta) return ''
  return [
    `原金额：${formatMaybeNumber(meta.amount)}`,
    `总天数：${formatMaybeNumber(meta.total_days)}`,
    `剩余天数：${formatMaybeNumber(meta.remaining_days)}`,
    `剩余比例：${formatMaybeNumber((meta.ratio || 0) * 100)}%`,
    `剩余价值：${formatMaybeNumber(meta.value)}`,
  ].join('\n')
})

function formatMaybeNumber(value: any) {
  const num = Number(value)
  if (!Number.isFinite(num)) return String(value ?? '-')
  return num.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}

async function ensureImageLoaded() {
  if (!imageUrl.value || objectUrl.value || imageFailed.value) return
  if (!imageUrl.value.startsWith('/api/')) return
  try {
    const blob = await fetchProtectedBlob(imageUrl.value)
    objectUrl.value = URL.createObjectURL(blob)
  } catch {
    imageFailed.value = true
  }
}

async function loadAndPreview() {
  manualLoaded.value = true
  await ensureImageLoaded()
  if (!imageFailed.value) previewVisible.value = true
}

async function downloadImage() {
  if (!imageUrl.value) return
  try {
    await downloadProtectedFile(imageUrl.value, filename.value)
  } catch {
    toast('图片下载失败', 'error')
  }
}

watch(
  () => [imageUrl.value, props.autoLoadImage] as const,
  async ([url, autoLoad]) => {
    if (objectUrl.value) {
      URL.revokeObjectURL(objectUrl.value)
      objectUrl.value = ''
    }
    imageFailed.value = false
    manualLoaded.value = false
    if (!url || !autoLoad) return
    await ensureImageLoaded()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  if (objectUrl.value) URL.revokeObjectURL(objectUrl.value)
})
</script>

<style scoped>
.empty-value {
  color: var(--text-faint);
}

.image-trigger {
  width: 26px;
  height: 18px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid var(--hairline);
  border-radius: 3px;
  background: var(--bg-elev);
  padding: 1px;
  vertical-align: middle;
  transition: all 0.15s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.image-trigger:hover,
.image-lazy:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(10, 10, 12, 0.08);
}

.image-loading {
  display: inline-block;
  width: 26px;
  height: 18px;
  vertical-align: middle;
  border: 1px solid var(--hairline);
  border-radius: 3px;
  background: linear-gradient(90deg, var(--bg-subtle) 25%, var(--bg-soft) 45%, var(--bg-subtle) 65%);
  background-size: 200% 100%;
  animation: img-shimmer 1.2s ease-in-out infinite;
}

@keyframes img-shimmer {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}

.image-trigger img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  border-radius: 2px;
}

.image-lazy {
  height: 18px;
  cursor: pointer;
  border: 1px dashed var(--ink-300);
  border-radius: 4px;
  color: var(--text-soft);
  background: var(--bg-elev);
  padding: 0 5px;
  font-size: 10px;
  font-weight: 500;
  transition: all 0.15s ease;
  display: inline-flex;
  align-items: center;
}

.image-missing {
  display: inline-flex;
  height: 18px;
  align-items: center;
  border: 1px solid var(--danger-border);
  border-radius: 3px;
  color: var(--danger);
  background: var(--danger-soft);
  padding: 0 5px;
  font-size: 10px;
}

.preview-body {
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

.preview-body img {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
}
</style>
