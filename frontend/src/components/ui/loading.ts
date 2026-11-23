/**
 * v-loading 指令 —— 替代 Element Plus 的 v-loading。
 * 在绑定元素上叠加一个自适应亮暗主题的加载遮罩层。
 */
import type { Directive, DirectiveBinding } from 'vue'

const OVERLAY_CLASS = 'app-loading-overlay'

function createOverlay(text?: string): HTMLElement {
  const overlay = document.createElement('div')
  overlay.className = OVERLAY_CLASS
  overlay.innerHTML = `
    <div class="d-flex flex-column align-items-center gap-2">
      <div class="spinner-border text-primary" role="status" aria-hidden="true"></div>
      ${text ? `<div class="small text-muted">${text}</div>` : ''}
    </div>`
  Object.assign(overlay.style, {
    position: 'absolute',
    inset: '0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'color-mix(in srgb, var(--bg-elev) 74%, transparent)',
    zIndex: '20',
    borderRadius: 'inherit',
  } as CSSStyleDeclaration)
  return overlay
}

function toggle(el: HTMLElement & { _loadingOverlay?: HTMLElement }, binding: DirectiveBinding) {
  const value = !!binding.value
  if (value) {
    if (!el._loadingOverlay) {
      const cs = getComputedStyle(el)
      if (cs.position === 'static') el.style.position = 'relative'
      const overlay = createOverlay(typeof binding.arg === 'string' ? binding.arg : undefined)
      el.appendChild(overlay)
      el._loadingOverlay = overlay
    }
  } else if (el._loadingOverlay) {
    el._loadingOverlay.remove()
    el._loadingOverlay = undefined
  }
}

export const vLoading: Directive = {
  mounted: toggle,
  updated: toggle,
  unmounted(el: HTMLElement & { _loadingOverlay?: HTMLElement }) {
    el._loadingOverlay?.remove()
    el._loadingOverlay = undefined
  },
}

export default vLoading
