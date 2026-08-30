import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发环境：前端(5173) → 后端(8000) 经 /api 代理联通
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
