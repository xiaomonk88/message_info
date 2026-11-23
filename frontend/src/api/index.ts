import http from './http'

export interface FieldType {
  type: string
  label: string
  description: string
  options_schema: Record<string, any>
}

export interface FieldDef {
  id: number
  code: string
  name: string
  type: string
  options?: Record<string, any> | null
  is_encrypted: boolean
  is_searchable: boolean
  enable_summary: boolean
  description?: string | null
  created_at: string
}

export interface ModuleFieldOut {
  id: number
  field_id: number
  sort_order: number
  is_required: boolean
  show_in_list: boolean
  column_width?: number | null
  field: FieldDef
}

export interface CalculatedFieldConfig {
  code: string
  name: string
  type: 'remaining_value_by_date'
  amount_field: string
  start_field: string
  end_field: string
  precision: number
  sort_order: number
  show_in_list: boolean
  enable_summary: boolean
}

export interface CategoryOut {
  id: number
  name: string
  icon?: string | null
  sort_order: number
  module_count: number
  created_at: string
}

export interface ModuleListItem {
  id: number
  code: string
  name: string
  icon?: string | null
  description?: string | null
  sort_order: number
  is_enabled: boolean
  auto_load_images: boolean
  category_id?: number | null
  created_at: string
  field_count: number
  record_count: number
}

export interface ModuleAccess {
  is_admin: boolean
  scope: 'own' | 'all'
  can_create: boolean
  can_edit_all: boolean
  can_delete_all: boolean
}

export interface ModuleOut extends ModuleListItem {
  fields: ModuleFieldOut[]
  calculated_fields: CalculatedFieldConfig[]
  access: ModuleAccess
}

export interface RecordOut {
  id: number
  module_id: number
  data: Record<string, any>
  is_deleted: boolean
  created_at: string
  updated_at: string
  created_by?: number | null
  owner?: string | null
  shared_count?: number
  can_edit: boolean
  can_delete: boolean
}

export type UserRole = 'admin' | 'member'

export interface UserOut {
  id: number
  username: string
  display_name?: string | null
  role: UserRole
  is_active: boolean
  created_at: string
  last_login_at?: string | null
  owned_records: number
  module_grants: number
  shared_records: number
}

export interface ModuleGrant {
  module_id: number
  scope: 'own' | 'all'
  can_create: boolean
  can_edit: boolean
  can_delete: boolean
  granted?: boolean
  shared_records?: number
}

export interface RecordAccess {
  owner_id?: number | null
  owner?: string | null
  shared: { user_id: number; username: string; display_name?: string | null; can_edit: boolean }[]
}

export interface MeOut {
  id: number
  username: string
  display_name?: string | null
  role: UserRole
}

export interface BackupFile {
  filename: string
  type: 'database' | 'full'
  size: number
  created_at: string
}

export interface BackupSchedule {
  enabled: boolean
  interval_hours: number
  last_run_at?: string | null
}

export interface AuditSettings {
  enabled: boolean
  max_count: number
  max_days: number
}

export interface SftpBackupConfig {
  enabled: boolean
  host: string
  port: number
  username: string
  auth_type: 'password' | 'private_key'
  password: string
  private_key: string
  private_key_passphrase: string
  remote_dir: string
  upload_on_manual: boolean
  upload_on_schedule: boolean
  has_password: boolean
  has_private_key: boolean
  has_private_key_passphrase: boolean
  last_sync_at?: string | null
  last_status?: string | null
  last_error?: string | null
  last_filename?: string | null
}

// ---------- Auth ----------
export interface TokenOut {
  access_token: string
  username: string
  role: UserRole
}

export const authApi = {
  login: (username: string, password: string) => http.post<TokenOut>('/auth/login', { username, password }),
  register: (data: { username: string; password: string; display_name?: string }) =>
    http.post<TokenOut>('/auth/register', data),
  settings: () => http.get<{ allow_register: boolean }>('/auth/settings'),
  updateSettings: (data: { allow_register: boolean }) =>
    http.put<{ allow_register: boolean }>('/auth/settings', data),
  me: () => http.get<MeOut>('/auth/me'),
  changePassword: (old_password: string, new_password: string) =>
    http.post('/auth/change-password', { old_password, new_password }),
  changeUsername: (password: string, new_username: string) =>
    http.post<{ ok: boolean; username: string }>('/auth/change-username', { password, new_username }),
}

// ---------- Categories ----------
export const categoryApi = {
  list: () => http.get<CategoryOut[]>('/categories'),
  create: (data: Partial<CategoryOut>) => http.post<CategoryOut>('/categories', data),
  update: (id: number, data: Partial<CategoryOut>) =>
    http.patch<CategoryOut>(`/categories/${id}`, data),
  remove: (id: number) => http.delete(`/categories/${id}`),
  reorder: (items: { id: number; sort_order: number }[]) =>
    http.post('/categories/reorder', { items }),
}

// ---------- Fields ----------
export const fieldApi = {
  types: () => http.get<FieldType[]>('/fields/types'),
  list: () => http.get<FieldDef[]>('/fields'),
  get: (id: number) => http.get<FieldDef>(`/fields/${id}`),
  create: (data: Partial<FieldDef>) => http.post<FieldDef>('/fields', data),
  update: (id: number, data: Partial<FieldDef>) => http.patch<FieldDef>(`/fields/${id}`, data),
  remove: (id: number) => http.delete(`/fields/${id}`),
}

// ---------- Modules ----------
export const moduleApi = {
  list: (params?: { category_id?: number; enabled_only?: boolean }, signal?: AbortSignal) =>
    http.get<ModuleListItem[]>('/modules', { params, signal }),
  get: (id: number, signal?: AbortSignal) => http.get<ModuleOut>(`/modules/${id}`, { signal }),
  create: (data: any) => http.post<ModuleOut>('/modules', data),
  update: (id: number, data: any) => http.patch<ModuleOut>(`/modules/${id}`, data),
  remove: (id: number) => http.delete(`/modules/${id}`),
  addField: (moduleId: number, data: any) =>
    http.post<ModuleFieldOut>(`/modules/${moduleId}/fields`, data),
  removeField: (moduleId: number, fieldId: number) =>
    http.delete(`/modules/${moduleId}/fields/${fieldId}`),
  updateField: (moduleId: number, fieldId: number, data: any) =>
    http.patch<ModuleFieldOut>(`/modules/${moduleId}/fields/${fieldId}`, data),
  reorderFields: (moduleId: number, items: { field_id: number; sort_order: number }[]) =>
    http.post(`/modules/${moduleId}/fields/reorder`, { items }),
}

// ---------- Records ----------
export const recordApi = {
  list: (
    moduleId: number,
    params?: { keyword?: string; page?: number; page_size?: number; sort?: string },
    signal?: AbortSignal
  ) =>
    http.get<{ items: RecordOut[]; total: number; page: number; page_size: number }>(
      `/modules/${moduleId}/records`,
      { params, signal }
    ),
  get: (moduleId: number, recordId: number, signal?: AbortSignal) =>
    http.get<RecordOut>(`/modules/${moduleId}/records/${recordId}`, { signal }),
  create: (moduleId: number, data: Record<string, any>) =>
    http.post<RecordOut>(`/modules/${moduleId}/records`, { data }),
  update: (moduleId: number, recordId: number, data: Record<string, any>) =>
    http.patch<RecordOut>(`/modules/${moduleId}/records/${recordId}`, { data }),
  remove: (moduleId: number, recordId: number) =>
    http.delete(`/modules/${moduleId}/records/${recordId}`),
  restore: (moduleId: number, recordId: number) =>
    http.post(`/modules/${moduleId}/records/${recordId}/restore`),
  purge: (moduleId: number, recordId: number) =>
    http.delete(`/modules/${moduleId}/records/${recordId}/purge`),
  trash: (moduleId: number, params?: { page?: number; page_size?: number }, signal?: AbortSignal) =>
    http.get<{ items: RecordOut[]; total: number }>(`/modules/${moduleId}/records/trash`, { params, signal }),
  search: (
    moduleId: number,
    data: {
      keyword?: string
      filters?: { field: string; op: string; value?: any }[]
      page?: number
      page_size?: number
    },
    signal?: AbortSignal
  ) =>
    http.post<{ items: RecordOut[]; total: number; page: number; page_size: number }>(
      `/modules/${moduleId}/records/search`,
      data,
      { signal }
    ),
  stats: (
    moduleId: number,
    data: {
      keyword?: string
      filters?: { field: string; op: string; value?: any }[]
      page?: number
      page_size?: number
    },
    signal?: AbortSignal
  ) =>
    http.post<{ sums: Record<string, number> }>(
      `/modules/${moduleId}/records/stats`,
      data,
      { signal }
    ),
  purgeTrash: (moduleId: number, ids: number[]) =>
    http.post<{ deleted: number }>(`/modules/${moduleId}/records/trash/purge`, { ids }),
  purgeAllTrash: (moduleId: number) =>
    http.post<{ deleted: number }>(`/modules/${moduleId}/records/trash/purge-all`),
  assign: (
    moduleId: number,
    data: { record_ids: number[]; user_ids: number[]; mode: 'share' | 'unshare' | 'transfer'; can_edit?: boolean }
  ) => http.post<{ ok: boolean; records: number; users: number }>(`/modules/${moduleId}/records/assign`, data),
  access: (moduleId: number, recordId: number) =>
    http.get<RecordAccess>(`/modules/${moduleId}/records/${recordId}/access`),
  setAccess: (moduleId: number, recordId: number, shared: { user_id: number; can_edit: boolean }[]) =>
    http.put<RecordAccess>(`/modules/${moduleId}/records/${recordId}/access`, { shared }),
}

// ---------- Users ----------
export const userApi = {
  list: () => http.get<UserOut[]>('/users'),
  create: (data: { username: string; password: string; display_name?: string; role: UserRole }) =>
    http.post<UserOut>('/users', data),
  update: (
    id: number,
    data: Partial<{ display_name: string | null; role: UserRole; is_active: boolean; password: string }>
  ) => http.patch<UserOut>(`/users/${id}`, data),
  remove: (id: number) => http.delete(`/users/${id}`),
  grants: (id: number) => http.get<ModuleGrant[]>(`/users/${id}/grants`),
  setGrants: (id: number, items: ModuleGrant[]) => http.put<ModuleGrant[]>(`/users/${id}/grants`, { items }),
}

// ---------- System ----------
export const systemApi = {
  info: () => http.get('/system/info'),
  audit: (params?: { page?: number; page_size?: number; entity_type?: string }) =>
    http.get('/system/audit-logs', { params }),
  auditSettings: () => http.get<AuditSettings>('/system/audit-settings'),
  updateAuditSettings: (data: AuditSettings) =>
    http.put<AuditSettings>('/system/audit-settings', data),
  clearAuditLogs: () => http.post<{ deleted: number }>('/system/audit-logs/clear'),
  backup: () => http.post('/system/backup'),
  fullBackup: () => http.post('/system/backup/full'),
  backups: () => http.get<{ items: BackupFile[] }>('/system/backups'),
  deleteBackup: (filename: string) => http.post('/system/backup/delete', { filename }),
  deleteAllBackups: () => http.post('/system/backups/delete'),
  restoreBackup: (filename: string) => http.post('/system/backup/restore', { filename }),
  backupSchedule: () => http.get<BackupSchedule>('/system/backup/schedule'),
  updateBackupSchedule: (data: { enabled: boolean; interval_hours: number }) =>
    http.put<BackupSchedule>('/system/backup/schedule', data),
  sftpConfig: () => http.get<SftpBackupConfig>('/system/backup/sftp'),
  updateSftpConfig: (data: Partial<SftpBackupConfig>) =>
    http.put<SftpBackupConfig>('/system/backup/sftp', data),
  testSftp: () => http.post('/system/backup/sftp/test'),
  syncLatestSftp: () => http.post('/system/backup/sftp/sync-latest'),
  downloadBackup: (filename: string) =>
    http.get(`/system/backup/download/${encodeURIComponent(filename)}`, { responseType: 'blob' }),
  clearAllRecords: (confirm: string) =>
    http.post<{ deleted_records: number; deleted_uploads: number }>(
      '/system/danger/clear-records',
      { confirm }
    ),
  clearAllData: (confirm: string) =>
    http.post<{
      deleted_records: number
      deleted_modules: number
      deleted_fields: number
      deleted_categories: number
      deleted_uploads: number
    }>('/system/danger/clear-all', { confirm }),
}

// ---------- Upload ----------
export const uploadApi = {
  upload: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post<{ path: string; url: string; filename: string; size: number; mime_type: string }>(
      '/upload',
      fd,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  },
}
