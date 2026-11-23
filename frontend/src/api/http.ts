import axios, { AxiosInstance } from 'axios'
import { toast } from '@/utils/ui'

const http: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (axios.isCancel(error) || error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError') {
      return Promise.reject(error)
    }
    const status = error?.response?.status
    const data = error?.response?.data
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      if (location.pathname !== '/login' && location.pathname !== '/register') location.href = '/login'
    }
    let detail = data?.detail
    if (typeof detail === 'object') {
      if (detail?.validation) {
        const first = Object.entries(detail.validation as Record<string, string>)[0]
        detail = first ? `${first[1]}` : '校验失败'
      } else {
        detail = JSON.stringify(detail)
      }
    }
    toast(detail || error.message || '请求失败', 'error')
    return Promise.reject(error)
  }
)

export default http
