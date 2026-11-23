export function resolveFileUrl(value: unknown) {
  if (!value) return ''
  const path = String(value)
  if (/^https?:\/\//i.test(path) || path.startsWith('data:') || path.startsWith('/api/')) return path
  return `/api/v1/files/${path.replace(/^\/+/, '')}`
}

export function fileNameFromPath(value: unknown, fallback = 'download') {
  const raw = String(value || '').split(/[\\/]/).pop()
  return raw || fallback
}

export async function fetchProtectedBlob(url: string) {
  const headers: HeadersInit = {}
  const token = localStorage.getItem('token')
  if (token && url.startsWith('/api/')) headers.Authorization = `Bearer ${token}`

  const response = await fetch(url, { headers })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.blob()
}

export async function downloadProtectedFile(url: string, filename: string) {
  const blob = await fetchProtectedBlob(url)
  const objectUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objectUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(objectUrl)
}
