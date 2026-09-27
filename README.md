# spiderAI

个人 AI 资讯收集与整理工具。目前已实现基础采集器、默认启用的 Qwen 摘要与重要性评分、SQLite 本地归档和本地资讯网页；已配置一小批试运行来源。

## 浏览资讯网页

`web/` 直接移植自 [SuYxh/ai-news-aggregator](https://github.com/SuYxh/ai-news-aggregator/tree/main/web) 的 React 前端，保留其页面布局、筛选、收藏、阅读历史与深色模式。SpiderAI 的 Python 服务从 SQLite 归档读取资讯并适配为前端数据格式。先在 `spiderAI` 目录安装并构建前端：

```bash
cd web
npm ci
npm run build
cd ..
```

然后启动本地页面：

```bash
python -m app.web
```

打开 `http://127.0.0.1:8765`。首次启动会自动创建 `data/spiderai.sqlite3`；启动页面不会运行采集器或调用 Qwen。空数据库会显示空资讯提示；按下文运行采集命令后，点击页面顶部刷新按钮即可读取新文章。临时检查单个 JSON 文件时，可用 `python -m app.web --snapshot data/ranked.json --port 8765`。

页面提供原版的 24 小时与 7 天视图、关键词搜索、来源分类与订阅源筛选、收藏、阅读历史和深色模式，并额外显示 SpiderAI 已有的排序分。文章跨采集批次保留，按链接去重；时间筛选优先使用原文发布时间，未知时使用首次收录时间。目前页面仍只提供 24 小时与 7 天窗口。收藏保存在 SQLite，首次打开新版页面会导入当前浏览器的旧收藏；阅读历史仍保存在浏览器。Python 服务只监听本机 `127.0.0.1`，提供页面、资讯查询与收藏接口。

## 采集资讯

入口为 `collecter.py`（保留项目指定拼写），支持 RSS、Atom、微信公众号 RSS 和单篇静态文章网页。先安装 `requirements.txt` 中的依赖，再在项目目录运行：

```bash
python collecter.py
```

直接运行会读取 `config/sources.json` 中已启用的来源，逐篇调用 Qwen 评分，并保存到 JSON 和 SQLite；运行前需在 `.env` 中配置 `WEMUST_API_KEY`。可用 `--sources 其他配置.json` 临时替换来源，用 `--no-score` 仅采集、不调用模型。每个来源填写 `name` 和 `url`，网页还可填写 `content_selector`（CSS 正文选择器）。来源应由用户维护，并按网站允许的方式和频率访问。

配置后默认输出 `data/articles-时间戳.json`，包含文章标题、链接、来源、发布时间、摘要、正文、采集时间及失败来源清单。RSS 只保留订阅源实际提供的内容，不自动请求每篇文章全文；网页不执行 JavaScript，也不自动遍历列表页。发布时间未知时留空。

每次运行保存独立 JSON 快照，并同步写入 `data/spiderai.sqlite3`；数据库按链接跨次去重，保留首次和最近收录时间。可用 `python collecter.py --output data/result.json` 指定 JSON 文件，同名文件会被覆盖。部分来源或评分失败时仍保存成功结果，并返回退出码 1，便于后续定时任务识别异常。旧命令中的 `--score` 仍可使用，但评分现已默认启用。

### 数据源规模与首批配置

[参考清单](docs/reference-sources.md)共 168 条记录，其中 70 个普通 RSS、53 个公众号 RSS、3 个 YouTube RSS 和 3 个示例 RSS 可由现有订阅解析器处理。这 129 个订阅源均已列入 [实际配置](config/sources.json)：76 个在 `rss`，53 个在 `wechat`。其余 39 条为平台/API 入口、辅助接口、替换及跳过规则；聚合页和接口需要专用适配器，替换及跳过规则不是独立文章来源。

考虑到第三方服务与模型调用量，当前仅启用 Qwen、DeepSeek、Anthropic 三个账号的转换 RSS，以及 OpenAI News、Hugging Face Blog 两个直连 RSS，其他 124 个条目保留为 `enabled: false`。每个条目均设有 `max_articles: 3`；有发布时间时先取最新文章，未知发布时间的条目保留原顺序。首批单次最多收录 15 篇，重复链接还会合并。之后可逐个修改 `enabled` 扩容，`max_articles` 可设为 1–100。示例来源的地址和历史状态未逐一验证，实际可用性需在试运行后确认。

```bash
python collecter.py
```

上面会采集、逐篇评分、生成快照并入库。增开来源会增加网络请求和模型调用量；当前首批最多处理 15 篇。

### 资讯重要性评分

在配置来源及 `WEMUST_API_KEY` 后，一次完成采集、评分和排序：

```bash
python collecter.py
```

也可以为已有采集快照评分；输出路径由你指定，同名文件会被覆盖：

```bash
python -m app.rank --input data/articles-示例.json --output data/ranked.json
```

模型对每篇文章给出四项 0–5 整数分及简短理由，程序按下表计算 0–100 总分。模型不能自行决定总分。只根据采集到的标题、来源摘要和正文判断；正文最多发送前 12000 字符，标题和来源摘要也有限长。资料不足时应保守给分。

| 维度 | 权重 | 判断依据 |
| --- | ---: | --- |
| AI 相关性 | 35% | 与 AI 技术或产业是否直接相关 |
| 影响力 | 30% | 对用户、行业或研究的潜在影响 |
| 新颖性 | 20% | 是否有明确的新发布或进展 |
| 信息证据 | 15% | 材料中的具体事实与可核查信息是否充分 |

内容分 `score` 为 `四项分数 × 各自权重 ÷ 5` 后四舍五入，范围 0–100；非 AI 资讯固定为 0 分。优先来源的 AI 资讯额外获得 10 分来源加分：`rank_score = score + source_bonus`。列表按 `rank_score` 降序排列，因此排序分最高可达 110；80 分及以上为“高”，60–79 分为“中”，其余为“低”，同分保留采集顺序。

优先来源包括[参考清单](docs/reference-sources.md)中的“中国AI公司”“AI Companies”“Dev Tools”三组共 40 个订阅源，以及 OpenAI News、Hugging Face Blog 两个官网示例订阅源。Hugging Face 的账号订阅位于“AI Companies”组。采集器保存原订阅地址，评分时与清单中的完整地址匹配；只匹配名称或共用的 RSS 转换服务域名不会加分。这些来源已登记在 `config/sources.json`，只有标记 `enabled: true` 的来源会采集。目录分类用于排序偏好，不等于对第三方 RSS 的官方身份认证。

`openai.com`、`anthropic.com` 及其子域名的文章链接也会自动识别为优先来源。其他公司的官方 RSS、公众号或第三方转换订阅，可在已人工确认的来源配置中添加 `ai_company`：

```json
{"wechat": [{"name": "官方账号", "url": "https://example.com/actual-feed", "ai_company": "公司名"}]}
```

请将示例 URL 和公司名替换为实际官方订阅信息。普通媒体转载、标题或正文提到公司名称不会自动获得加分；与 AI 无关的公司文章也不加分。同时命中参考清单和官网只加一次 10 分。`ai_company` 是维护来源的人作出的身份标记，程序不会独立核验该账号。

输出 `articles` 中每篇包含 `score`、`source_bonus`、`rank_score`、`priority_source`（命中的参考编号或公司）、`official_ai_company`、`priority` 和 `ai_analysis`（摘要、分类、标签、各项分数、权重、理由），顶层 `ranking` 记录模型、权重、来源加分和成功/失败数量。单篇模型失败时原文仍保留在末尾，分数为 `null`，并记录 `scoring_error`；命令退出码为 1。

每篇文章通常调用一次 Qwen；如果输出被长度上限截断，会提高上限再试一次，因此会产生相应的 API 用量和等待时间。来源或评分失败会写入快照并使命令返回非零退出码，不会被当作成功。终端会显示前十条，评分结果同步入库，网页刷新后展示分数。分数是基于已采集材料的排序辅助，不代表外部事实核验；调整权重后可对旧快照重新运行评分命令。

离线测试：`python -m unittest discover -s tests -v`。实际网站的提取效果需在提供来源后进一步验证。

### 微信公众号与来源筛选

参考 [SuYxh/ai-news-aggregator 的公众号模块](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts)，接入的是第三方 RSS 转换服务，不需要微信 Cookie；默认评分仍需要 Qwen key，使用 `--no-score` 时不需要。它也不支持仅凭公众号名称下载任意历史文章。

- [完整数据源清单](docs/reference-sources.md)：包含名称、RSS/URL、类型、上游文件出处及可恢复的历史状态，按类别和编号筛选。
- [机器可读候选目录](docs/reference-sources.json)：只用于参考，所有记录均标记为未启用，不会自动采集。
- [实际采集配置](config/sources.json)：`rss`、`url`、`wechat` 三组中已登记 129 条订阅源，首批启用 5 条。

选定公众号后，在 `config/sources.json` 的 `wechat` 列表中添加包含 `name`（公众号名称）、`url`（实际 RSS 地址）、可选 `category`（账号类别）的对象；可选 `enabled: false` 表示暂不采集。然后运行：

```bash
python collecter.py
```

默认读取 `config/sources.json`；指定 `--sources` 后可使用其他配置，错误配置会在联网前被拒绝。所有文章保存 `source_type`（`rss`、`url` 或 `wechat`）供网页分类；公众号条目还保存 `feed_url` 和 `category`。这里的类别指账号类别，AI 对单篇文章的分类使用独立字段。

正文只在 RSS 提供时保存，不自动访问微信原文页面；无逐篇发布时间时保留 `null`，不会将 RSS 的 `lastBuildDate` 冒充文章发布时间。第三方服务的更新频率、覆盖范围和可用性会影响结果。

候选清单来自固定提交的公开源码和公开状态快照，未将全部候选逐一联网验证。聚合网站入口及 API 需要单独适配，不能直接作为单篇文章 URL 使用；上游动态发现的下游源并没有完整固定清单。

## 调用 Qwen

根据用户提供的《WeMust AI API 使用指南》（PDF 页眉日期 2026-02-11，第 5–6、23、87–90 页），平台提供兼容 OpenAI Chat Completions 格式的 HTTP JSON 接口：

- 方法：`POST`
- 地址：`https://ai-apigateway.must.edu.mo/openhub/v1/chat/completions`
- 认证：`Authorization: Bearer <API key>`
- 模型：固定使用用户指定的 `Qwen3.6-35B-A3B`，不会自动切换其他模型。

该指南没有列出这个 Qwen 模型；截至 2026-09-27，本项目已用实际 key 成功调用模型并完成资讯评分。账号的剩余额度仍需在平台查看。平台整体支持工具调用，不代表每个模型都支持；本模块使用普通文本对话，不依赖工具调用或 JSON 模式。

使用 Python 3.10 或更高版本，在终端进入本目录：

```bash
cd SpiderAI
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp -n .env.example .env
```

在编辑器中打开 `.env`，填写 `WEMUST_API_KEY=你的实际key`，不需要加 Bearer 前缀。程序也支持同名环境变量，且环境变量优先；不要把真实 key 写进代码。

普通问答：

```bash
python -m app.qwen --prompt "你好，请用一句话介绍你能如何帮助整理AI资讯。"
```

整理已有正文（示例文件为明确标记的虚构资讯）：

```bash
python -m app.qwen --article examples/article.txt
```

结果显示中文摘要、分类、标签、AI 相关性以及接口返回的 token 用量。程序检查 JSON 字段；不合格或被截断的结果会报错，不会写入数据库。示例正文上限为 30000 字符，这是应用限制，并非模型上下文规格。

后续在爬虫中复用：

```python
from app.qwen import QwenClient

client = QwenClient.from_env()
result = client.summarize("这里放爬虫已经获取的文章正文")
print(result["article"]["summary"])
```

代码位置：`app/qwen.py`。连接超时为 10 秒，等待响应超时为 120 秒；普通问答和摘要只发送一次请求，资讯评分仅在输出被截断时提高上限再试一次。网络或服务错误不会自动重试。401 检查 key，403 检查权限，400/404 检查模型标识和接口，429 检查频率与配额。

运行离线测试（使用模拟响应，不调用平台、不消耗额度）：

```bash
python -m unittest discover -s tests -v
```

## 第一版目标

- 每日从少量经过人工筛选的权威来源收集新资讯，优先使用 RSS 或官方 API，没有时再解析网页。
- 浏览历史资讯，按关键词、来源、日期筛选，支持已读、收藏和笔记。
- 先做个人本地使用版本；自动摘要、多用户和云部署后续再考虑。

## SQLite 本地归档

```text
权威来源 → Python 采集 → 清洗与去重 → SQLite
                                        ↕
                                 Python HTTP API
                                        ↕
                               React/TypeScript 页面
```

Python 采集器与页面服务共用 `app/db.py`；SQLite 是 Python 标准库的一部分，不需要运行数据库服务器。建表 SQL 位于 `migrations/001_initial.sql`。采集器仍是独立命令，打开网页不会触发抓取。

旧 JSON 快照可以批量导入，重复导入同一文章不会增加文章总数：

```bash
python -m app.db init
python -m app.db import data/articles-*.json data/ranked.json
```

只导入实际存在的文件；若没有 `data/ranked.json`，从命令中删去该路径。`init` 可省略，采集和网页启动时也会自动建库。数据库使用 WAL 模式，采集写入时网页可继续读取。

网页只查询 24 小时或 7 天内文章的标题、链接、来源和时间等列表字段，不把完整正文载入页面服务内存。首次迁移浏览器旧收藏后开始计时，每隔 7 天自动删除**首次收录超过 7 天且未收藏**的数据库文章；已收藏的文章始终保留。服务持续运行时每小时检查是否到期，服务关闭期间错过的检查会在下次启动或采集时补做。清理后尝试压缩 SQLite 文件，释放磁盘空间。

`data/` 目录内的采集与评分 JSON 快照自最后写入起保留 3 天；超过 3 天后，在下次采集、评分、网页启动或网页运行期间的每小时检查中自动删除。其他目录中的 JSON 不受影响。SQLite 的 7 天未收藏文章规则单独执行，已收藏文章不会因快照删除而丢失。过期快照删除后不能再用它重新评分；可用 `du -sh data` 查看整个目录的占用。数据库文章清理前必须先打开新版页面，让旧浏览器收藏迁入 SQLite；迁移成功后再等一个完整的 7 天周期，避免立即误删旧收藏文章。

## 关键目录

```text
spiderAI/
├── README.md
├── .gitignore
├── app/
│   ├── db.py             # SQLite 建库、入库与历史查询
│   └── web.py            # 本地静态页面与只读资讯接口
├── web/                 # 移植的 React/TypeScript 前端
├── config/              # 来源列表及其类型
├── migrations/          # 建表 SQL，提交 Git
├── data/                # SQLite、WAL 文件和 JSON 快照，不提交 Git
└── tests/               # 解析、去重等关键逻辑测试
```

## 数据设计

当前有四张表：

- `articles`：标题、原文链接（唯一）、来源、发布时间、首次及最近收录时间、排序分和完整文章 JSON。
- `collection_runs`：采集时间、失败来源清单和快照哈希。
- `favorites`：已收藏链接、标题和收藏时间；独立于文章保存，供清理规则判断。
- `maintenance`：记录旧收藏迁移状态和上次清理时间。

时间统一保存为 UTC，展示时由浏览器转换为本地时区。发布时间未知时留空；同一链接重复抓取会更新最近收录时间和文章内容，不会新增第二条。不同来源对同一事件的不同链接分别保留。

## 后续实现顺序

1. 增加超出 7 天的收藏历史检索、已读和笔记 API，把剩余的浏览器本地状态逐步迁移到数据库。
2. 增加每日调度、超时、有限重试和错误日志；一个来源失败不影响其他来源。电脑关机时本地调度无法运行，若需持续自动采集再部署到常开机器。
3. 在可靠采集基础上持久化 AI 摘要、分类和日报；生成摘要与来源摘要分开保存，保留原文链接。

权威性通过人工维护来源名单控制，优先第一手公告与研究发布；收录不等同于认可内容。网页采集应遵守来源的访问和使用规则，并设置合理频率。

## 版本管理

提交代码、配置示例和建表 SQL；`spiderAI/.gitignore` 忽略整个 `data/`、SQLite 文件及 `-wal`/`-shm` 伴随文件，也忽略 `.env`、日志和虚拟环境。可在仓库根目录运行 `git check-ignore -v spiderAI/data/spiderai.sqlite3` 检查规则。`.gitignore` 只对未被 Git 跟踪的文件生效；若以前提交过数据库，需要先用 `git rm --cached` 将其移出索引，再提交。数据库仅在本机，换机器或重装前请自行备份 `data/`。当前文件夹位于已有 Git 仓库内，无需创建嵌套仓库。

## 技术参考

- [Python sqlite3 官方文档](https://docs.python.org/3/library/sqlite3.html)
