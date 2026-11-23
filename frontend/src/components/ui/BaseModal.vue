<template>
  <teleport to="body">
    <!-- Drawer 模式 → Offcanvas -->
    <div
      v-if="drawer"
      ref="rootEl"
      class="offcanvas offcanvas-end"
      tabindex="-1"
      :style="widthStyle"
    >
      <div class="offcanvas-header border-bottom">
        <h5 class="offcanvas-title">{{ title }}</h5>
        <button type="button" class="btn-close" @click="hide"></button>
      </div>
      <div class="offcanvas-body">
        <slot />
      </div>
      <div v-if="$slots.footer" class="offcanvas-footer border-top p-3 d-flex justify-content-end gap-2">
        <slot name="footer" />
      </div>
    </div>

    <!-- 普通模态 -->
    <div v-else ref="rootEl" class="modal fade" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable" :class="sizeClass">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ title }}</h5>
            <button type="button" class="btn-close" @click="hide"></button>
          </div>
          <div class="modal-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="modal-footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as bootstrap from 'bootstrap'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title?: string
    size?: '' | 'sm' | 'lg' | 'xl' | 'fullscreen'
    drawer?: boolean
    width?: string
    closeOnBackdrop?: boolean
  }>(),
  { title: '', size: '', drawer: false, width: '', closeOnBackdrop: true }
)

const emit = defineEmits<{
  'update:modelValue': [boolean]
  opened: []
  closed: []
}>()

const rootEl = ref<HTMLElement>()
let instance: bootstrap.Modal | bootstrap.Offcanvas | null = null

const sizeClass = computed(() => (props.size ? `modal-${props.size}` : ''))
const widthStyle = computed(() => (props.drawer && props.width ? { width: props.width } : undefined))

function hide() {
  instance?.hide()
}

onMounted(() => {
  if (!rootEl.value) return
  if (props.drawer) {
    instance = new bootstrap.Offcanvas(rootEl.value, {
      backdrop: props.closeOnBackdrop ? true : 'static',
    })
  } else {
    instance = new bootstrap.Modal(rootEl.value, {
      backdrop: props.closeOnBackdrop ? true : 'static',
    })
  }
  const showEvt = props.drawer ? 'shown.bs.offcanvas' : 'shown.bs.modal'
  const hideEvt = props.drawer ? 'hidden.bs.offcanvas' : 'hidden.bs.modal'
  rootEl.value.addEventListener(showEvt, () => emit('opened'))
  rootEl.value.addEventListener(hideEvt, () => {
    emit('update:modelValue', false)
    emit('closed')
  })
  if (props.modelValue) instance.show()
})

watch(
  () => props.modelValue,
  (v) => {
    if (!instance) return
    if (v) instance.show()
    else instance.hide()
  }
)

onBeforeUnmount(() => {
  instance?.hide()
  instance?.dispose()
  instance = null
})
</script>
