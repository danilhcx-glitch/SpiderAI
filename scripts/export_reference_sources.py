"""从参考项目本地快照导出候选来源和可读清单，不修改实际采集配置。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


# 明确区分网页入口和 API；这些聚合入口不能直接当成单篇文章 URL 使用。
PLATFORMS = [
    ("AI今日热榜", "https://aihot.today/", "网页聚合", "aihot.ts"),
    ("TechURLs", "https://techurls.com/", "网页聚合", "techurls.ts"),
    ("NewsNow", "https://newsnow.busiyi.world/", "网页入口", "newsnow.ts"),
    ("NewsNow 批量 API", "https://newsnow.busiyi.world/api/s/entire", "POST API", "newsnow.ts"),
    ("NewsNow 单源 API", "https://newsnow.busiyi.world/api/s?id=${sid}", "GET API 模板", "newsnow.ts"),
    ("TopHub", "https://tophub.today/", "网页聚合", "tophub.ts"),
    ("Buzzing", "https://www.buzzing.cc/feed.json", "JSON Feed", "buzzing.ts"),
    ("Info Flow", "https://iris.findtruman.io/web/info_flow", "动态发现 RSS", "iris.ts"),
    ("Zeli", "https://zeli.app/api/hacker-news?type=hot24h", "GET API", "zeli.ts"),
    ("AI HubToday", "https://ai.hubtoday.app/", "网页日报", "aihubtoday.ts"),
    ("AIbase", "https://www.aibase.com/zh/news", "网页聚合", "aibase.ts"),
    ("BestBlogs", "https://api.bestblogs.dev/api/newsletter/list", "POST API", "bestblogs.ts"),
    ("BestBlogs 阅读地址", "https://www.bestblogs.dev/en/newsletter#${issueId}", "输出链接模板", "bestblogs.ts"),
    ("新智元", "https://aiera.com.cn/wp-json/wp/v2/posts?per_page=100&page=${page}", "分页 GET API", "xinzhiyuan.ts"),
    ("WaytoAGI", "https://waytoagi.feishu.cn/wiki/QPe5w5g7UisbEkkow8XcDmOpn8e?fromScene=spaceOverview", "飞书知识库", "../config.ts"),
    ("WaytoAGI 历史更新", "https://waytoagi.feishu.cn/wiki/FjiOwWp2giA7hRk6jjfcPioCnAc", "飞书备用入口", "../config.ts"),
    ("Hacker News 时间补全", "https://hacker-news.firebaseio.com/v0/item/${id}.json", "辅助 API 模板", "newsnow.ts"),
    ("GitHub 时间补全", "https://api.github.com/repos/${cleanPath}", "辅助 API 模板", "newsnow.ts"),
    ("少数派时间补全", "https://sspai.com/feed", "辅助 RSS", "newsnow.ts"),
]


def markdown_cell(value: object) -> str:
    """转义表格分隔符及换行，避免来源名称破坏 Markdown。"""
    return str(value).replace("|", "\\|").replace("\n", " ")


def export(repo: Path, opml_path: Path, status_path: Path, output: Path) -> None:
    """提取当前参考版本的显式来源，并记录原始位置和历史状态。"""
    revision = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True,
    ).strip()
    base = f"https://github.com/SuYxh/ai-news-aggregator/blob/{revision}/"
    groups = json.loads(opml_path.read_text(encoding="utf-8"))
    status = json.loads(status_path.read_text(encoding="utf-8"))
    states = {row["feed_url"]: row for row in status["rss_opml"]["feeds"]}
    records = []

    def add(name: str, url: str, kind: str, category: str, origin: str, **extra) -> None:
        """添加未启用的候选项，编号仅用于本次清单筛选。"""
        records.append({"id": f"S{len(records) + 1:03d}", "name": name, "url": url,
                        "kind": kind, "category": category, "origin": origin,
                        "enabled": False, **extra})

    for group in groups:
        for feed in group["feeds"]:
            state = states.get(feed["url"], {})
            if state.get("skipped"):
                historical = "上游快照跳过"
            elif state.get("ok") is False:
                historical = "上游快照失败"
            elif state.get("ok"):
                historical = f"上游快照 {state.get('item_count', 0)} 条"
            else:
                historical = "无状态"
            add(feed["name"], feed["url"], "RSS", group["name"], "data/opml-feeds.json",
                historical_status=historical,
                effective_url=state.get("effective_feed_url", feed["url"]))

    # 工作流从 secret 恢复 OPML；公开 JSON 与状态文件交叉核对，防止只列到示例源。
    known = {row["url"] for row in records}
    for row in states.values():
        if row["feed_url"] not in known:
            add(row["feed_title"], row["feed_url"], "RSS", "状态文件补充", "data/source-status.json")

    wechat_text = (repo / "src/fetchers/wechat-rss.ts").read_text(encoding="utf-8")
    wechat = re.findall(r"\{ name: '([^']+)', url: '([^']+)', category: '([^']+)' \}", wechat_text)
    if not wechat:
        raise ValueError("未识别公众号配置，需检查上游格式变化")
    for name, url, category in wechat:
        add(name, url, "微信公众号 RSS", category, "src/fetchers/wechat-rss.ts")

    youtube = (repo / "src/fetchers/youtube.ts").read_text(encoding="utf-8")
    for match in re.finditer(r"name: (['\"])(.*?)\1, channelId: '([^']+)'", youtube):
        name, channel = match.group(2), match.group(3)
        add(name, f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}",
            "YouTube RSS", "视频", "src/fetchers/youtube.ts",
            home_url=f"https://www.youtube.com/channel/{channel}")

    for node in ET.parse(repo / "feeds/follow.example.opml").iter("outline"):
        if node.get("xmlUrl"):
            add(node.get("title", node.get("text", "")), node.get("xmlUrl"), "示例 RSS",
                "OPML 示例", "feeds/follow.example.opml", home_url=node.get("htmlUrl", ""))
    for name, url, kind, filename in PLATFORMS:
        origin = "src/config.ts" if filename.startswith("../") else f"src/fetchers/{filename}"
        add(name, url, kind, "平台与接口", origin)

    config = (repo / "src/config.ts").read_text(encoding="utf-8")
    replacements = re.findall(r"'(https?://[^']+)': '(https?://[^']+)'", config)
    for before, after in replacements:
        add(before, after, "替换 RSS", "原项目替换规则", "src/config.ts", original_url=before)
    for section, label in [("skipPrefixes", "跳过前缀"), ("skipExact", "跳过地址")]:
        block = re.search(rf"{section}:.*?\[(.*?)\]", config, re.S)
        for url in re.findall(r"'(https?://[^']+)'", block.group(1)):
            add(url, url, label, "原项目跳过规则", "src/config.ts")

    output.mkdir(parents=True, exist_ok=True)
    document = {"repository": "https://github.com/SuYxh/ai-news-aggregator",
                "revision": revision, "upstream_status_at": status["generated_at"],
                "note": "候选目录中的 enabled 均为 false；实际启用状态见 config/sources.json，来源未逐一验证可用性。",
                "sources": records}
    (output / "reference-sources.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    lines = ["# 参考项目数据源筛选清单", "",
             f"参考版本：`{revision}`。所有编号均为本次清单编号。", "",
             f"[参考仓库](https://github.com/SuYxh/ai-news-aggregator)，状态快照时间：`{status['generated_at']}`。", "",
             # 清单记录仍是候选快照，采集开关以实际配置文件为准。
             "这是公开源码与已提交数据中可恢复的数据源清单；其中 129 个可直接处理的订阅源已登记到 `config/sources.json`，首批启用 5 个。",
             "历史成功状态不代表现在可用；第三方转发 RSS 也不等于官方 RSS。",
             # 导出时保留项目自己的评分约定，避免重新生成清单后说明消失。
             "评分时，‘中国AI公司’‘AI Companies’‘Dev Tools’三组及 OpenAI News、Hugging Face Blog 两个官网示例订阅源可获得来源优先级加分。仅对实际启用并采集的来源生效。", "",
             f"包含 {len(states)} 个 OPML 来源、{len(wechat)} 个公众号、3 个 YouTube 频道、3 个 OPML 示例，另列平台接口、替换及跳过规则。",
             "上游 README 称 52 个公众号，但该版本源码实际配置 53 个；本清单以源码为准。", "",
             "`feeds/follow.opml` 本身未提交，由工作流从 secret 恢复；这里用公开的 `data/opml-feeds.json` 与 `data/source-status.json` 交叉核对。",
             "Info Flow 会从远端页面动态发现 RSS；NewsNow、TopHub、TechURLs、AI今日热榜等平台还会动态发现下游来源，源码没有固定完整子清单。这里列出它们的入口和接口，不把历史文章 URL 当作订阅源。", "",
             "筛选时告诉我来源名称或编号即可。RSS 可直接接入；聚合首页、JSON Feed、POST API、飞书页需要各自适配，不能直接放进单篇文章 URL 配置。", "",
             "## 分组统计", "", "| 类别 | 条数 |", "|---|---:|"]
    for kind, count in Counter(row["kind"] for row in records).items():
        lines.append(f"| {kind} | {count} |")
    for category in dict.fromkeys(row["category"] for row in records):
        lines += ["", f"## {category}", "", "| 编号 | 名称 | 类型 | RSS / URL | 备注与出处 |", "|---|---|---|---|---|"]
        for row in records:
            if row["category"] != category:
                continue
            note = row.get("historical_status", "未逐一验证")
            if row.get("original_url"):
                note += f"；原地址：{row['original_url']}"
            if row.get("home_url"):
                note += f"；网页：{row['home_url']}"
            note += f"；[源码]({base}{row['origin']})"
            lines.append("| " + " | ".join(markdown_cell(x) for x in
                         [row["id"], row["name"], row["kind"], row["url"], note]) + " |")
    lines += ["", "## 公众号接入说明", "",
              "参考项目读取第三方 decemberpei.cyou 的公众号 RSS，不登录微信，也不直接拉取任意公众号的历史记录。spiderAI 独立实现相同订阅流程，复用已有 feedparser 解析器，不复制上游 TypeScript 实现。",
              "逐篇文章优先使用 RSS 中的发布时间；未知时为 null，不采用上游将 lastBuildDate 作为每篇发布时间的做法。", ""]
    (output / "reference-sources.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"导出 {len(records)} 条候选/规则，公众号 {len(wechat)} 个，OPML {len(states)} 个。")


def main() -> None:
    """接收本地参考快照位置，离线生成清单文件。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--opml-json", type=Path, required=True)
    parser.add_argument("--status-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export(args.repo, args.opml_json, args.status_json, args.output)


if __name__ == "__main__":
    # 此脚本仅导出文档，不抓取候选网站，也不启用来源。
    main()
