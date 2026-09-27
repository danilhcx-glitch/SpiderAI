// 构建时先处理 Tailwind 类名，再补齐必要的浏览器前缀。
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
