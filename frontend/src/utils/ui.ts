/**
 * UI 工具：toast / confirm / alert / prompt
 * 基于 Bootstrap 5 的 Toast 与 Modal，替代 Element Plus 的 ElMessage / ElMessageBox。
 * 本模块不依赖 Vue，也不导入 http，避免循环依赖。
 */
import * as bootstrap from 'bootstrap'

type ToastType = 'success' | 'warning' | 'error' | 'info'

// lucide 图标内联 SVG（此模块拼 HTML 字符串，无法使用 Vue 组件）
const ICON_PATH: Record<ToastType, string> = {
  success: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  warning:
    '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 20h16a2 2 0 0 0 1.73-2Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  error: '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
}

function iconSvg(type: ToastType, extraClass = ''): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide ${extraClass}">${ICON_PATH[type]}</svg>`
}

function ensureToastContainer(): HTMLElement {
  let c = document.getElementById('app-toast-container')
  if (!c) {
    c = document.createElement('div')
    c.id = 'app-toast-container'
    c.className = 'position-fixed top-0 end-0 p-3'
    c.style.zIndex = '1090'
    document.body.appendChild(c)
  }
  return c
}

export function toast(message: string, type: ToastType = 'info', delay = 3000): void {
  const container = ensureToastContainer()
  const el = document.createElement('div')
  el.className = 'toast app-toast'
  el.setAttribute('role', 'alert')
  el.setAttribute('aria-live', 'assertive')
  el.setAttribute('aria-atomic', 'true')
  el.innerHTML = `
    <span class="toast-icon ${type}">${iconSvg(type)}</span>
    <span class="toast-msg">${escapeHtml(message)}</span>
    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>`
  container.appendChild(el)
  const t = new bootstrap.Toast(el, { delay })
  el.addEventListener('hidden.bs.toast', () => el.remove())
  t.show()
}

export const message = {
  success: (m: string) => toast(m, 'success'),
  warning: (m: string) => toast(m, 'warning'),
  error: (m: string) => toast(m, 'error'),
  info: (m: string) => toast(m, 'info'),
}

interface ConfirmOptions {
  title?: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
  html?: boolean
}

function buildModal(innerBody: string, footer: string): { modal: bootstrap.Modal; root: HTMLElement } {
  const root = document.createElement('div')
  root.className = 'modal fade'
  root.tabIndex = -1
  root.innerHTML = `
    <div class="modal-dialog modal-dialog-centered app-dialog-dialog">
      <div class="modal-content">
        ${innerBody}
        <div class="modal-footer app-dialog-footer">${footer}</div>
      </div>
    </div>`
  document.body.appendChild(root)
  const modal = new bootstrap.Modal(root, { backdrop: 'static' })
  root.addEventListener('hidden.bs.modal', () => {
    modal.dispose()
    root.remove()
  })
  return { modal, root }
}

/** 「图标 chip + 标题 + 正文」竖排的对话框主体 */
function dialogBody(opts: {
  icon: ToastType
  chip: '' | 'success' | 'warning' | 'danger'
  title: string
  content: string
  closeAct: string
}): string {
  return `
    <button type="button" class="btn-close app-dialog-x" data-act="${opts.closeAct}" aria-label="Close"></button>
    <div class="app-dialog-body">
      <span class="app-dialog-icon ${opts.chip}">${iconSvg(opts.icon)}</span>
      <h5 class="app-dialog-title">${escapeHtml(opts.title)}</h5>
      <div class="app-dialog-text">${opts.content}</div>
    </div>`
}

/** 替代 ElMessageBox.confirm —— 返回 Promise<boolean> */
export function confirm(message: string, opts: ConfirmOptions = {}): Promise<boolean> {
  const {
    title = '请确认',
    confirmText = '确定',
    cancelText = '取消',
    danger = false,
    html = false,
  } = opts
  const body = dialogBody({
    icon: danger ? 'warning' : 'info',
    chip: danger ? 'danger' : '',
    title,
    content: html ? message : escapeHtml(message),
    closeAct: 'cancel',
  })
  const footer = `
    <button type="button" class="btn btn-outline-secondary" data-act="cancel">${escapeHtml(cancelText)}</button>
    <button type="button" class="btn ${danger ? 'btn-danger' : 'btn-primary'}" data-act="ok">${escapeHtml(confirmText)}</button>`
  const { modal, root } = buildModal(body, footer)
  return new Promise<boolean>((resolve) => {
    let result = false
    root.addEventListener('click', (e) => {
      const act = (e.target as HTMLElement).closest('[data-act]')?.getAttribute('data-act')
      if (act === 'ok') {
        result = true
        modal.hide()
      } else if (act === 'cancel') {
        modal.hide()
      }
    })
    root.addEventListener('hidden.bs.modal', () => resolve(result), { once: true })
    modal.show()
  })
}

interface AlertOptions {
  title?: string
  confirmText?: string
  type?: ToastType
  html?: boolean
}

/** 替代 ElMessageBox.alert —— 单按钮，返回 Promise<void> */
export function alert(message: string, opts: AlertOptions = {}): Promise<void> {
  const { title = '提示', confirmText = '知道了', type, html = false } = opts
  const iconType: ToastType = type ?? 'info'
  const chip = iconType === 'error' ? 'danger' : iconType === 'info' ? '' : iconType
  const body = dialogBody({
    icon: iconType,
    chip,
    title,
    content: html ? message : escapeHtml(message),
    closeAct: 'ok',
  })
  const footer = `<button type="button" class="btn btn-primary" data-act="ok">${escapeHtml(confirmText)}</button>`
  const { modal, root } = buildModal(body, footer)
  return new Promise<void>((resolve) => {
    root.addEventListener('click', (e) => {
      if ((e.target as HTMLElement).closest('[data-act="ok"]')) modal.hide()
    })
    root.addEventListener('hidden.bs.modal', () => resolve(), { once: true })
    modal.show()
  })
}

interface PromptOptions {
  title?: string
  confirmText?: string
  cancelText?: string
  placeholder?: string
  defaultValue?: string
  danger?: boolean
}

/** 替代 ElMessageBox.prompt —— 带输入框，返回 Promise<string|null>（取消返回 null） */
export function prompt(message: string, opts: PromptOptions = {}): Promise<string | null> {
  const {
    title = '请输入',
    confirmText = '确定',
    cancelText = '取消',
    placeholder = '',
    defaultValue = '',
    danger = false,
  } = opts
  const body = dialogBody({
    icon: danger ? 'warning' : 'info',
    chip: danger ? 'danger' : '',
    title,
    content: `${escapeHtml(message)}
      <input type="text" class="form-control" data-role="prompt-input"
             placeholder="${escapeHtml(placeholder)}" value="${escapeHtml(defaultValue)}" />`,
    closeAct: 'cancel',
  })
  const footer = `
    <button type="button" class="btn btn-outline-secondary" data-act="cancel">${escapeHtml(cancelText)}</button>
    <button type="button" class="btn ${danger ? 'btn-danger' : 'btn-primary'}" data-act="ok">${escapeHtml(confirmText)}</button>`
  const { modal, root } = buildModal(body, footer)
  const input = root.querySelector<HTMLInputElement>('[data-role="prompt-input"]')!
  return new Promise<string | null>((resolve) => {
    let result: string | null = null
    const submit = () => {
      result = input.value
      modal.hide()
    }
    root.addEventListener('click', (e) => {
      const act = (e.target as HTMLElement).closest('[data-act]')?.getAttribute('data-act')
      if (act === 'ok') submit()
      else if (act === 'cancel') modal.hide()
    })
    input.addEventListener('keyup', (e) => {
      if (e.key === 'Enter') submit()
    })
    root.addEventListener('shown.bs.modal', () => input.focus(), { once: true })
    root.addEventListener('hidden.bs.modal', () => resolve(result), { once: true })
    modal.show()
  })
}

function escapeHtml(s: string): string {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export default { toast, message, confirm, alert, prompt }
