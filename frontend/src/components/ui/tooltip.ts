/**
 * v-tip 指令 —— 替代 Element Plus 的 el-tooltip。
 * 包装 Bootstrap Tooltip，按元素 init/update/dispose。
 * 用法：v-tip="'提示文本'"  或  v-tip:top="'文本'"
 */
import type { Directive, DirectiveBinding } from 'vue'
import * as bootstrap from 'bootstrap'

interface TipEl extends HTMLElement {
  _tip?: bootstrap.Tooltip
}

function create(el: TipEl, binding: DirectiveBinding) {
  const title = binding.value == null ? '' : String(binding.value)
  if (!title) return
  el.setAttribute('title', title)
  el._tip = new bootstrap.Tooltip(el, {
    title,
    placement: (binding.arg as any) || 'top',
    trigger: 'hover focus',
    container: 'body',
  })
}

function destroy(el: TipEl) {
  el._tip?.dispose()
  el._tip = undefined
  // dispose 会还原 title 属性，动态切空值时避免残留原生提示
  el.removeAttribute('title')
}

export const vTip: Directive = {
  mounted: create,
  updated(el: TipEl, binding) {
    if (binding.value === binding.oldValue) return
    destroy(el)
    create(el, binding)
  },
  unmounted: destroy,
}

export default vTip
