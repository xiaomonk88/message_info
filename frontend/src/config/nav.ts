/**
 * 共享导航配置 —— 系统管理区的固定入口。
 * Layout 侧边栏、面包屑、CommandPalette 与配置流程条共用，避免多处硬编码。
 */
import type { Component } from 'vue'
import { Archive, Folder, History, LayoutGrid, List, ShieldCheck, Users } from 'lucide-vue-next'

export type NavGroupKey = 'structure' | 'ops'

export interface SystemNavItem {
  to: string
  label: string
  icon: Component
  group: NavGroupKey
  desc: string
  /** 仅管理员可见 */
  admin: boolean
}

export const NAV_GROUPS: { key: NavGroupKey; label: string }[] = [
  { key: 'structure', label: '结构配置' },
  { key: 'ops', label: '系统运维' },
]

export const SYSTEM_NAV: SystemNavItem[] = [
  { to: '/admin/categories', label: '分类管理', icon: Folder, group: 'structure', desc: '侧边栏分组与排序', admin: true },
  { to: '/admin/fields', label: '字段管理', icon: List, group: 'structure', desc: '全局可复用的字段库', admin: true },
  { to: '/admin/modules', label: '板块管理', icon: LayoutGrid, group: 'structure', desc: '数据表与字段组合', admin: true },
  { to: '/admin/users', label: '用户管理', icon: Users, group: 'ops', desc: '账号、注册开关与权限分配', admin: true },
  { to: '/admin/backups', label: '数据备份', icon: Archive, group: 'ops', desc: '快照、定时与异地容灾', admin: true },
  { to: '/admin/audit', label: '操作日志', icon: History, group: 'ops', desc: '关键操作流水与保留策略', admin: true },
  { to: '/admin/account', label: '账号安全', icon: ShieldCheck, group: 'ops', desc: '登录凭据与危险操作', admin: false },
]

/** 按角色过滤可见的系统入口 */
export function systemNavFor(isAdmin: boolean) {
  return SYSTEM_NAV.filter((item) => isAdmin || !item.admin)
}

export function findSystemNav(path: string) {
  return SYSTEM_NAV.find((item) => item.to === path)
}

export function navGroupLabel(key: NavGroupKey) {
  return NAV_GROUPS.find((g) => g.key === key)?.label || ''
}
