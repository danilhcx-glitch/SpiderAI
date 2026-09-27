# 前端来源

本目录从 [SuYxh/ai-news-aggregator 的 `web/`](https://github.com/SuYxh/ai-news-aggregator/tree/0b7d2ea7b392aab434f523e0fa05470d3ee15185/web) 复制，参考提交：`0b7d2ea7b392aab434f523e0fa05470d3ee15185`。

SpiderAI 的适配集中在以下部分：

- `src/hooks/useNewsData.ts` 从本地 `/api/news` 读取两种时间范围的数据，默认显示全部来源，并让手动刷新绕过缓存。
- `src/components/` 保留原页面结构，调整品牌文字、实际来源说明和排序分展示。
- `vite.config.ts` 在开发模式转发数据请求到 Python 服务；构建文件由 `app/web.py` 提供。
- `index.html` 移除原站点访问统计脚本；`src/utils/analytics.ts` 仅保留原组件调用的兼容接口。
- `src/` 中的中文注释说明移植代码的职责与 SpiderAI 适配规则。

原项目的其余采集代码和公开数据未复制到 SpiderAI。
