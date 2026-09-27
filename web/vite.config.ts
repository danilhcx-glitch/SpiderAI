// 开发模式由 Vite 提供页面，并把只读数据请求转发给 SpiderAI Python 服务。
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://127.0.0.1:8765',
      '/data': 'http://127.0.0.1:8765',
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
