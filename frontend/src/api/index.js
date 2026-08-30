import axios from 'axios'

// 后端 RESTful API 封装（开发环境经 Vite /api 代理到 FastAPI:8000）
const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 统一错误处理：提取后端 detail 字段作为错误信息
http.interceptors.response.use(
  (resp) => resp.data,
  (err) => {
    const detail = err?.response?.data?.detail
    const msg = typeof detail === 'string'
      ? detail
      : (err.message || '请求失败')
    return Promise.reject(new Error(msg))
  }
)

// ---- 质量检测 ----
export const detect = (curve) => http.post('/detect', curve)
export const detectBatch = (curves) => http.post('/detect/batch', { curves })

// ---- 数据接入 ----
export const ingest = (curve) => http.post('/ingest', curve)
export const ingestFile = (spec, file) => {
  const fd = new FormData()
  fd.append('spec', spec)
  fd.append('file', file)
  return http.post('/ingest/file', fd)
}

// ---- 工艺追溯 ----
export const trace = (query) => http.post('/trace', query)
export const stats = () => http.get('/stats')

// ---- 参数优化 ----
export const optimize = (spec) => http.post('/optimize', { spec })
export const correlation = () => http.get('/correlation')

export default http
