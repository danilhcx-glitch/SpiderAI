# 参考项目数据源筛选清单

参考版本：`6d2277cab2a6828810fd54cdd2962e3109628e38`。所有编号均为本次清单编号。

[参考仓库](https://github.com/SuYxh/ai-news-aggregator)，状态快照时间：`2026-09-26T08:54:55.189Z`。

这是公开源码与已提交数据中可恢复的数据源清单；其中 129 个可直接处理的订阅源已登记到 `config/sources.json`，首批启用 5 个。
历史成功状态不代表现在可用；第三方转发 RSS 也不等于官方 RSS。
评分时，‘中国AI公司’‘AI Companies’‘Dev Tools’三组及 OpenAI News、Hugging Face Blog 两个官网示例订阅源可获得来源优先级加分。仅对实际启用并采集的来源生效。

包含 70 个 OPML 来源、53 个公众号、3 个 YouTube 频道、3 个 OPML 示例，另列平台接口、替换及跳过规则。
上游 README 称 52 个公众号，但该版本源码实际配置 53 个；本清单以源码为准。

`feeds/follow.opml` 本身未提交，由工作流从 secret 恢复；这里用公开的 `data/opml-feeds.json` 与 `data/source-status.json` 交叉核对。
Info Flow 会从远端页面动态发现 RSS；NewsNow、TopHub、TechURLs、AI今日热榜等平台还会动态发现下游来源，源码没有固定完整子清单。这里列出它们的入口和接口，不把历史文章 URL 当作订阅源。

筛选时告诉我来源名称或编号即可。RSS 可直接接入；聚合首页、JSON Feed、POST API、飞书页需要各自适配，不能直接放进单篇文章 URL 配置。

## 分组统计

| 类别 | 条数 |
|---|---:|
| RSS | 70 |
| 微信公众号 RSS | 53 |
| YouTube RSS | 3 |
| 示例 RSS | 3 |
| 网页聚合 | 4 |
| 网页入口 | 1 |
| POST API | 2 |
| GET API 模板 | 1 |
| JSON Feed | 1 |
| 动态发现 RSS | 1 |
| GET API | 1 |
| 网页日报 | 1 |
| 输出链接模板 | 1 |
| 分页 GET API | 1 |
| 飞书知识库 | 1 |
| 飞书备用入口 | 1 |
| 辅助 API 模板 | 2 |
| 辅助 RSS | 1 |
| 替换 RSS | 8 |
| 跳过前缀 | 10 |
| 跳过地址 | 2 |

## 中文博客

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S001 | 量子位 | RSS | https://www.qbitai.com/feed | 上游快照失败；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S002 | 宝玉的分享 | RSS | https://baoyu.io/feed.xml | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S003 | 爱范儿 | RSS | http://www.ifanr.com/feed | 上游快照 20 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S004 | 阮一峰的网络日志 | RSS | http://feeds.feedburner.com/ruanyifeng | 上游快照 6 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S005 | 美团技术团队 | RSS | https://tech.meituan.com/feed/ | 上游快照 0 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S006 | SuperTechFans | RSS | https://www.supertechfans.com/cn/index.xml | 上游快照 5 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |

## 中文聚合

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S007 | 掘金本周最热 | RSS | https://rsshub.bestblogs.dev/juejin/trending/all/weekly | 上游快照 20 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |

## 中文Twitter博主

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S008 | 李继刚(@lijigang_com) | RSS | https://api.xgo.ing/rss/user/ca2fa444b6ea4b8b974fe148056e497a | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S009 | 宝玉(@dotey) | RSS | https://api.xgo.ing/rss/user/97f1484ae48c430fbbf3438099743674 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S010 | 歸藏(guizang.ai)(@op7418) | RSS | https://api.xgo.ing/rss/user/831fac36aa0a49a9af79f35dc1c9b5d9 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S011 | 小互(@imxiaohu) | RSS | https://api.xgo.ing/rss/user/74e542992cf7441390c708f5601071d4 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S012 | 向阳乔木(@vista8) | RSS | https://api.xgo.ing/rss/user/9de19c78f7454ad08c956c1a00d237fe | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S013 | AI产品黄叔(@PMbackttfuture) | RSS | https://api.xgo.ing/rss/user/5b632b7fba274f62928cdcc9d3db4c5e | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S014 | idoubi(@idoubicc) | RSS | https://api.xgo.ing/rss/user/3d72acd51d21414ea39871fc01982a65 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S015 | Viking(@vikingmute) | RSS | https://api.xgo.ing/rss/user/aab44cb2665a49258cd81f63b0b55192 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S016 | Geek(@geekbb) | RSS | https://api.xgo.ing/rss/user/9cb3b60e689e4445a7fbdfd0be144126 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S017 | Tw93(@HiTw93) | RSS | https://api.xgo.ing/rss/user/665fc88440fd4436acbc2e630d824926 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S018 | Yangyi(@Yangyixxxx) | RSS | https://api.xgo.ing/rss/user/66c40de71a9842fda4853b7d9d1d20da | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S019 | hidecloud(@hidecloud) | RSS | https://api.xgo.ing/rss/user/23d41992b29340788aa3d09d8364c5f5 | 上游快照 39 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S020 | cat(@_catwu) | RSS | https://api.xgo.ing/rss/user/66a6b39ddcfa42e39621e0ab293c1bdd | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S021 | meng shao(@shao__meng) | RSS | https://api.xgo.ing/rss/user/48aae530e0bf413aa7d44380f418e2e3 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S022 | Eric Jing(@ericjing_ai) | RSS | https://api.xgo.ing/rss/user/ddfdcdd4e390495c942f0b5da62af0fb | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |

## 中国AI公司

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S023 | Qwen(@Alibaba_Qwen) | RSS | https://api.xgo.ing/rss/user/80032d016d654eb4afe741ff34b7643d | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S024 | DeepSeek(@deepseek_ai) | RSS | https://api.xgo.ing/rss/user/68b610deb24b47ae9a236811563cda86 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S025 | Hunyuan(@TXhunyuan) | RSS | https://api.xgo.ing/rss/user/6e8e7b42cb434818810f87bcf77d86fb | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S026 | Skywork(@Skywork_ai) | RSS | https://api.xgo.ing/rss/user/6d7d398dd80b48d79669c92745d32cf6 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S027 | Kling AI(@Kling_ai) | RSS | https://api.xgo.ing/rss/user/564237c3de274d58a04f064920817888 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S028 | Hailuo AI (MiniMax)(@Hailuo_AI) | RSS | https://api.xgo.ing/rss/user/e65b5e59fcb544918c1ba17f5758f0f8 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S029 | Fish Audio(@FishAudio) | RSS | https://api.xgo.ing/rss/user/4900b3dcd592424687582ff9e0f148ea | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S030 | Monica_IM(@hey_im_monica) | RSS | https://api.xgo.ing/rss/user/5d749cc613ec4069bb2a47334739e1b6 | 上游快照 19 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S031 | Dify(@dify_ai) | RSS | https://api.xgo.ing/rss/user/0be252fedbe84ad7bea21be44b18da89 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S032 | Jina AI(@JinaAI_) | RSS | https://api.xgo.ing/rss/user/f510f6e7eecf456ca7e2895a46752888 | 上游快照 29 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S033 | Milvus(@milvusio) | RSS | https://api.xgo.ing/rss/user/424e67b19eed4500b7a440976bbd2ade | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |

## 华人AI研究者

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S034 | Fei-Fei Li(@drfeifei) | RSS | https://api.xgo.ing/rss/user/a4bfe44bfc0d4c949da21ebd3f5f42a5 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S035 | Junyang Lin(@JustinLin610) | RSS | https://api.xgo.ing/rss/user/082097117b4543e9a741cd2580f936d3 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S036 | Binyuan Hui(@huybery) | RSS | https://api.xgo.ing/rss/user/f54b2b40185943ce8f48a880110b7bc2 | 上游快照 25 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S037 | Jim Fan(@DrJimFan) | RSS | https://api.xgo.ing/rss/user/c6cfe7c0d6b74849997073233fdea840 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S038 | Jerry Liu(@jerryjliu0) | RSS | https://api.xgo.ing/rss/user/b3d904c0d7c446558ef3a1e7f2eb362b | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S039 | Lilian Weng(@lilianweng) | RSS | https://api.xgo.ing/rss/user/a8f7e2238039461cbc8bf55f5f194498 | 上游快照 32 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S040 | Andrew Ng(@AndrewYNg) | RSS | https://api.xgo.ing/rss/user/08b5488b20bc437c8bfc317a52e5c26d | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S041 | Hung-yi Lee | RSS | https://www.youtube.com/feeds/videos.xml?channel_id=UC2ggjtuuWvxrHHHiaDH1dlQ | 上游快照 15 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |

## AI Companies

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S042 | OpenAI(@OpenAI) | RSS | https://api.xgo.ing/rss/user/0c0856a69f9f49cf961018c32a0b0049 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S043 | OpenAI Developers(@OpenAIDevs) | RSS | https://api.xgo.ing/rss/user/971dc1fc90da449bac23e5fad8a33d55 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S044 | ChatGPT(@ChatGPTapp) | RSS | https://api.xgo.ing/rss/user/f7992687b8d74b14bf2341eb3a0a5ec4 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S045 | Anthropic(@AnthropicAI) | RSS | https://api.xgo.ing/rss/user/fc28a211471b496682feff329ec616e5 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S046 | Claude(@claudeai) | RSS | https://api.xgo.ing/rss/user/01f60d63a61b44d692cc35c7feb0b4a4 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S047 | Google AI(@GoogleAI) | RSS | https://api.xgo.ing/rss/user/4de0bd2d5cef4333a0260dc8157054a7 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S048 | Google DeepMind(@GoogleDeepMind) | RSS | https://api.xgo.ing/rss/user/a99538443a484fcc846bdcc8f50745ec | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S049 | Google Gemini App(@GeminiApp) | RSS | https://api.xgo.ing/rss/user/6fb337feeec44ca38b79491b971d868d | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S050 | xAI(@xai) | RSS | https://api.xgo.ing/rss/user/3953aa71e87a422eb9d7bf6ff1c7c43e | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S051 | Hugging Face(@huggingface) | RSS | https://api.xgo.ing/rss/user/fc16750ce50741f1b1f05ea1fb29436f | 上游快照 48 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S052 | NVIDIA AI(@NVIDIAAI) | RSS | https://api.xgo.ing/rss/user/05f1492e43514dc3862a076d3697c390 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S053 | AI at Meta(@AIatMeta) | RSS | https://api.xgo.ing/rss/user/ef7c70f9568d45f4915169fef4ce90b4 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S054 | Microsoft Research(@MSFTResearch) | RSS | https://api.xgo.ing/rss/user/61f4b78554fb4b8fa5653ec5d924d15a | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S055 | Groq Inc(@GroqInc) | RSS | https://api.xgo.ing/rss/user/771b32075fe54a83bdb6966de9647b4f | 上游快照 26 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S056 | Cursor(@cursor_ai) | RSS | https://api.xgo.ing/rss/user/5287b4e0e13a4ab7ab7b1d56f9d88960 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S057 | Windsurf(@windsurf_ai) | RSS | https://api.xgo.ing/rss/user/4a8273800ed34a069eecdb6c5c1b9ccf | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S058 | bolt.new(@boltdotnew) | RSS | https://api.xgo.ing/rss/user/760ab7cd9708452c9ce1f9144b92a430 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |

## Dev Tools

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S059 | LangChain(@LangChainAI) | RSS | https://api.xgo.ing/rss/user/862fee50a745423c87e2633b274caf1d | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S060 | LlamaIndex(@llama_index) | RSS | https://api.xgo.ing/rss/user/67e259bd5be544ce84bbc867eace54c2 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S061 | ollama(@ollama) | RSS | https://api.xgo.ing/rss/user/6326c63a2dfa445bbde88bea0c3112c2 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S062 | Firecrawl(@firecrawl_dev) | RSS | https://api.xgo.ing/rss/user/c04abb206bbf4f91b22795024d6c0614 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S063 | Browser Use(@browser_use) | RSS | https://api.xgo.ing/rss/user/b8d7530f0b294405825013bbc1cc198f | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S064 | OpenRouter(@OpenRouterAI) | RSS | https://api.xgo.ing/rss/user/e503a90c035c4b1d8f8dd34907d15bf4 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S065 | AI SDK(@aisdk) | RSS | https://api.xgo.ing/rss/user/22af005b21ec45b1a4503acca777b7f0 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S066 | DeepLearning.AI(@DeepLearningAI) | RSS | https://api.xgo.ing/rss/user/42e6b4901b97498eab2ab64c07d56177 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S067 | GitHub(@github) | RSS | https://api.xgo.ing/rss/user/fa5b15f68a2e4df1ab301e26a4ab9190 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S068 | Figma(@figma) | RSS | https://api.xgo.ing/rss/user/f8a106a09a7d404fb8de7eb0c5ddd2a2 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S069 | Notion(@NotionHQ) | RSS | https://api.xgo.ing/rss/user/f97a26863aec4425b021720d4f8e4ede | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |
| S070 | NotebookLM(@NotebookLM) | RSS | https://api.xgo.ing/rss/user/221a88341acb475db221a12fed8208d0 | 上游快照 50 条；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/data/opml-feeds.json) |

## AI

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S071 | 机器之心 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-jiqizhixin.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S072 | 量子位 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-liangziwei.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S073 | 新智元 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-xinzhiyuan.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S074 | DeepTech深科技 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-shenkeji.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S075 | PaperWeekly | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-paperweekly.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S076 | 计算机视觉life | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-jisuanjishijuelife.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S077 | AI前线 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-aiqianxian.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S078 | 夕小瑶科技说 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-xixiaoyaokejishuo.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S079 | 海外独角兽 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-haiwaidujiaoshou.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S080 | 甲子光年 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-jiaziguangnian.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S081 | 集智俱乐部 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-jizhijvlebu.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |

## 科技媒体

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S082 | 晚点LatePost | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-wandian.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S083 | 36氪 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-36ke.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S084 | 36氪Pro | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-sanliukepro.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S085 | 虎嗅App | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-huxiuapp.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S086 | 极客公园 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-jikegongyuan.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S087 | 少数派 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-shaoshupai.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S088 | APPSO | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-appso.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S089 | 爱范儿 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-anfaner.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S090 | 差评 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-chaping.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S091 | 钛媒体 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-taimeiti.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |

## 技术开发

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S092 | InfoQ | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-infoq.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S093 | 阿里云开发者 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-aliyunkaifazhe.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S094 | 腾讯技术工程 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-tengxunjishugongcheng.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S095 | 前端之巅 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-qianduanzhidian.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S096 | 架构师之路 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-jiagoushizhilu.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S097 | GitHubDaily | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-githubdaily.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |

## 财经投资

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S098 | 华尔街见闻 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-huaerjiejianwen.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S099 | 财经杂志 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-caijingzazhi.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S100 | 第一财经YiMagazine | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-diyicaijing.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S101 | 经纬创投 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-jingweichuangtou.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S102 | 红杉汇 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-hongshanhui.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S103 | 42章经 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-sierzhangjing.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S104 | 远川投资评论 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-chuanyuanyouzipinglun.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S105 | 泽平宏观展望 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-zepinghongguanzhanwang.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |

## 个人博主

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S106 | caoz的梦呓 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-caozdemengyi.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S107 | L先生说 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-lxianshengshuo.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S108 | 槽边往事 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-caobianwangshi.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S109 | 孟岩 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-mengyan.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S110 | 刘润 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-liurun.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S111 | 辉哥奇谭 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-huigeqitan.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S112 | warfalcon | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-warfalcon.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S113 | 玉树芝兰 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-yushuzhilan.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S114 | 九边 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-jiubian.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S115 | 也谈钱 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-yetanqian.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S116 | keso怎么看 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-kesozenmekan.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S117 | 阑夕 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-lanxi.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |

## 产品商业

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S118 | 人人都是产品经理 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-renrendoushichanpinjingli.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S119 | 互联网怪盗团 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-hulianwangguaidaotuan.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S120 | 乱翻书 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-luanfanshu.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S121 | 刘言飞语 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-liuyanfeiyu.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S122 | 产品犬舍 | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-chanpinquanshe.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |
| S123 | FounderPark | 微信公众号 RSS | https://decemberpei.cyou/rssbox/wechat-founderpark.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/wechat-rss.ts) |

## 视频

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S124 | Peter Yang | YouTube RSS | https://www.youtube.com/feeds/videos.xml?channel_id=UCnpBg7yqNauHtlNSpOl5-cg | 未逐一验证；网页：https://www.youtube.com/channel/UCnpBg7yqNauHtlNSpOl5-cg；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/youtube.ts) |
| S125 | Lenny's Podcast | YouTube RSS | https://www.youtube.com/feeds/videos.xml?channel_id=UC6t1O76G0jYXOAoYCm153dA | 未逐一验证；网页：https://www.youtube.com/channel/UC6t1O76G0jYXOAoYCm153dA；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/youtube.ts) |
| S126 | 20VC | YouTube RSS | https://www.youtube.com/feeds/videos.xml?channel_id=UCf0PBRjhf0rF8fWBIxTuoWA | 未逐一验证；网页：https://www.youtube.com/channel/UCf0PBRjhf0rF8fWBIxTuoWA；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/youtube.ts) |

## OPML 示例

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S127 | OpenAI News | 示例 RSS | https://openai.com/news/rss.xml | 未逐一验证；网页：https://openai.com/news；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/feeds/follow.example.opml) |
| S128 | Hugging Face Blog | 示例 RSS | https://huggingface.co/blog/feed.xml | 未逐一验证；网页：https://huggingface.co/blog；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/feeds/follow.example.opml) |
| S129 | InfoQ CN | 示例 RSS | https://www.infoq.cn/feed | 未逐一验证；网页：https://www.infoq.cn/；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/feeds/follow.example.opml) |

## 平台与接口

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S130 | AI今日热榜 | 网页聚合 | https://aihot.today/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/aihot.ts) |
| S131 | TechURLs | 网页聚合 | https://techurls.com/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/techurls.ts) |
| S132 | NewsNow | 网页入口 | https://newsnow.busiyi.world/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/newsnow.ts) |
| S133 | NewsNow 批量 API | POST API | https://newsnow.busiyi.world/api/s/entire | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/newsnow.ts) |
| S134 | NewsNow 单源 API | GET API 模板 | https://newsnow.busiyi.world/api/s?id=${sid} | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/newsnow.ts) |
| S135 | TopHub | 网页聚合 | https://tophub.today/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/tophub.ts) |
| S136 | Buzzing | JSON Feed | https://www.buzzing.cc/feed.json | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/buzzing.ts) |
| S137 | Info Flow | 动态发现 RSS | https://iris.findtruman.io/web/info_flow | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/iris.ts) |
| S138 | Zeli | GET API | https://zeli.app/api/hacker-news?type=hot24h | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/zeli.ts) |
| S139 | AI HubToday | 网页日报 | https://ai.hubtoday.app/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/aihubtoday.ts) |
| S140 | AIbase | 网页聚合 | https://www.aibase.com/zh/news | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/aibase.ts) |
| S141 | BestBlogs | POST API | https://api.bestblogs.dev/api/newsletter/list | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/bestblogs.ts) |
| S142 | BestBlogs 阅读地址 | 输出链接模板 | https://www.bestblogs.dev/en/newsletter#${issueId} | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/bestblogs.ts) |
| S143 | 新智元 | 分页 GET API | https://aiera.com.cn/wp-json/wp/v2/posts?per_page=100&page=${page} | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/xinzhiyuan.ts) |
| S144 | WaytoAGI | 飞书知识库 | https://waytoagi.feishu.cn/wiki/QPe5w5g7UisbEkkow8XcDmOpn8e?fromScene=spaceOverview | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S145 | WaytoAGI 历史更新 | 飞书备用入口 | https://waytoagi.feishu.cn/wiki/FjiOwWp2giA7hRk6jjfcPioCnAc | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S146 | Hacker News 时间补全 | 辅助 API 模板 | https://hacker-news.firebaseio.com/v0/item/${id}.json | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/newsnow.ts) |
| S147 | GitHub 时间补全 | 辅助 API 模板 | https://api.github.com/repos/${cleanPath} | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/newsnow.ts) |
| S148 | 少数派时间补全 | 辅助 RSS | https://sspai.com/feed | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/fetchers/newsnow.ts) |

## 原项目替换规则

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S149 | https://rsshub.app/infoq/recommend | 替换 RSS | https://www.infoq.cn/feed | 未逐一验证；原地址：https://rsshub.app/infoq/recommend；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S150 | https://rsshub.app/huggingface/blog-zh | 替换 RSS | https://huggingface.co/blog/feed.xml | 未逐一验证；原地址：https://rsshub.app/huggingface/blog-zh；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S151 | https://rsshub.app/readhub/daily | 替换 RSS | https://readhub.cn/rss | 未逐一验证；原地址：https://rsshub.app/readhub/daily；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S152 | https://rsshub.app/36kr/hot-list | 替换 RSS | https://36kr.com/feed | 未逐一验证；原地址：https://rsshub.app/36kr/hot-list；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S153 | https://rsshub.app/sspai/index | 替换 RSS | https://sspai.com/feed | 未逐一验证；原地址：https://rsshub.app/sspai/index；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S154 | https://rsshub.app/sspai/matrix | 替换 RSS | https://sspai.com/feed | 未逐一验证；原地址：https://rsshub.app/sspai/matrix；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S155 | https://rsshub.app/meituan/tech | 替换 RSS | https://tech.meituan.com/feed | 未逐一验证；原地址：https://rsshub.app/meituan/tech；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S156 | https://mjg59.dreamwidth.org/data/rss | 替换 RSS | http://mjg59.dreamwidth.org/data/rss | 未逐一验证；原地址：https://mjg59.dreamwidth.org/data/rss；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |

## 原项目跳过规则

| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |
|---|---|---|---|---|
| S157 | https://rsshub.app/telegram/channel/ | 跳过前缀 | https://rsshub.app/telegram/channel/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S158 | https://rsshub.app/jike/ | 跳过前缀 | https://rsshub.app/jike/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S159 | https://rsshub.app/bilibili/ | 跳过前缀 | https://rsshub.app/bilibili/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S160 | https://rsshub.app/zhihu/ | 跳过前缀 | https://rsshub.app/zhihu/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S161 | https://rsshub.app/xiaoyuzhou/podcast/ | 跳过前缀 | https://rsshub.app/xiaoyuzhou/podcast/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S162 | https://rsshub.app/xyzrank | 跳过前缀 | https://rsshub.app/xyzrank | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S163 | https://rsshub.app/mittrchina/hot | 跳过前缀 | https://rsshub.app/mittrchina/hot | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S164 | https://wechat2rss.bestblogs.dev/ | 跳过前缀 | https://wechat2rss.bestblogs.dev/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S165 | https://werss.bestblogs.dev/ | 跳过前缀 | https://werss.bestblogs.dev/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S166 | http://47.122.94.119:18080/ | 跳过前缀 | http://47.122.94.119:18080/ | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S167 | https://rachelbythebay.com/w/atom.xml | 跳过地址 | https://rachelbythebay.com/w/atom.xml | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |
| S168 | https://flak.tedunangst.com/rss | 跳过地址 | https://flak.tedunangst.com/rss | 未逐一验证；[源码](https://github.com/SuYxh/ai-news-aggregator/blob/6d2277cab2a6828810fd54cdd2962e3109628e38/src/config.ts) |

## 公众号接入说明

参考项目读取第三方 decemberpei.cyou 的公众号 RSS，不登录微信，也不直接拉取任意公众号的历史记录。spiderAI 独立实现相同订阅流程，复用已有 feedparser 解析器，不复制上游 TypeScript 实现。
逐篇文章优先使用 RSS 中的发布时间；未知时为 null，不采用上游将 lastBuildDate 作为每篇发布时间的做法。
