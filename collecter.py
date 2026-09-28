"""采集资讯并默认调用配置的模型评分，再将结果保存为 JSON 与 SQLite 归档。"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlsplit

import feedparser
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 来源由 config/sources.json 维护；网页 URL 应指向文章，暂不自动遍历列表页。
# 来源格式：{"name": "来源名称", "url": "实际地址"}。
# 网页来源还可填写 content_selector，例如 article，用于精确定位正文。
# 官方 AI 公司账号可填写 ai_company，供评分时识别第三方 RSS 中的原始发布者。
# max_articles 限制单个来源单次收录的条目数，避免首次运行导入大量历史资讯。

ROOT = Path(__file__).resolve().parent
LOGGER = logging.getLogger("spiderAI.collecter")
MAX_BYTES = 5 * 1024 * 1024  # 限制单次响应大小，避免异常页面占用过多内存。


def normalize_url(value: str, base: str = "") -> str:
    """解析相对链接并移除片段；仅接收不含账号密码的 HTTP(S) 地址。"""
    url = urldefrag(urljoin(base, value.strip()))[0]
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("来源或文章链接必须是有效的 HTTP(S) 地址")
    if parts.username or parts.password:
        raise ValueError("链接不得包含账号密码")
    return url


def clean_html(value: str) -> str:
    """去除脚本、样式等非正文元素，把 HTML 转为纯文本。"""
    soup = BeautifulSoup(value, "html.parser")
    for node in soup.select("script, style, noscript, template"):
        node.decompose()
    return " ".join(soup.stripped_strings)


def create_session() -> requests.Session:
    """创建复用连接的客户端；只对 GET 的临时网络或服务错误有限重试。"""
    session = requests.Session()
    session.headers["User-Agent"] = "spiderAI/0.1 (personal news collector)"
    retry = Retry(
        total=2, backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"], respect_retry_after_header=False,
    )
    # 使用有限退避，避免远端 Retry-After 导致任务长时间挂起。
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch(session: requests.Session, url: str) -> tuple[bytes, str, str | None]:
    """下载内容，返回字节、重定向后的地址和显式编码；失败时抛出异常。"""
    with session.get(normalize_url(url), timeout=(10, 30), stream=True) as response:
        response.raise_for_status()
        chunks = []
        size = 0
        for chunk in response.iter_content(chunk_size=65536):
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError("响应超过 5 MB 上限")
            chunks.append(chunk)
        # 未声明编码时交给 HTML 解析器检测，避免 requests 默认编码造成乱码。
        content_type = response.headers.get("Content-Type", "")
        encoding = response.encoding if "charset=" in content_type.lower() else None
        return b"".join(chunks), normalize_url(response.url), encoding


def parse_feed(data: bytes, source: dict[str, str], base: str) -> list[dict]:
    """读取 RSS 或 Atom；坏条目跳过，无法识别的订阅源报错。"""
    feed = feedparser.parse(data)
    if not feed.version:
        raise ValueError("响应不是可识别的 RSS/Atom 订阅源")
    if feed.bozo:
        LOGGER.warning("订阅源格式不规范，尝试保留可解析的条目：%s", source["name"])
    articles = []
    for entry in feed.entries:
        title = clean_html(entry.get("title", ""))
        link = entry.get("link", "")
        if not title or not link:
            continue
        try:
            url = normalize_url(link, base)
        except ValueError:
            continue
        published = entry.get("published_parsed")
        # 发布时间未知时留空，不用抓取时间或更新时间冒充发布时间。
        published_at = (
            datetime(*published[:6], tzinfo=timezone.utc).isoformat()
            if published else None
        )
        content = entry.get("content", [])
        articles.append({
            "title": title, "url": url, "source": source["name"],
            "published_at": published_at,
            "summary": clean_html(entry.get("summary", "")),
            "content": clean_html(content[0].get("value", "")) if content else "",
        })
    return articles


def parse_page(
    data: bytes, source: dict[str, str], url: str, encoding: str | None = None,
) -> list[dict]:
    """提取单篇静态网页；可配置 CSS 正文选择器，不执行 JavaScript。"""
    soup = BeautifulSoup(data, "html.parser", from_encoding=encoding)
    title_node = soup.select_one("h1") or soup.title
    title = title_node.get_text(" ", strip=True) if title_node else ""
    selector = source.get("content_selector")
    body = soup.select_one(selector) if selector else (
        soup.select_one("article") or soup.select_one("main")
    )
    if body is None or not title:
        raise ValueError("未找到标题或正文；请配置 content_selector 或使用文章 URL")
    # 尽量去除正文容器内的导航和表单；通用规则仍需按实际网站校准。
    for node in body.select("nav, footer, aside, form"):
        node.decompose()
    content = clean_html(str(body))
    if not content:
        raise ValueError("网页正文为空，可能需要 JavaScript 渲染")
    description = soup.select_one('meta[name="description"]')
    date_node = soup.select_one('meta[property="article:published_time"]')
    published_at = None
    if date_node and date_node.get("content"):
        try:
            date = datetime.fromisoformat(date_node["content"].replace("Z", "+00:00"))
            # 无时区的日期无法准确转换为 UTC，保留为空以避免猜测。
            if date.tzinfo:
                published_at = date.astimezone(timezone.utc).isoformat()
        except ValueError:
            pass
    return [{
        "title": title, "url": url, "source": source["name"],
        "published_at": published_at,
        "summary": clean_html(description.get("content", "")) if description else "",
        "content": content,
    }]


def parse_wechat_feed(data: bytes, source: dict[str, str], base: str) -> list[dict]:
    """解析公众号 RSS，保留账号类别及订阅地址；不把源更新时间当作发布时间。"""
    # 复用成熟的 RSS/Atom 解析器，兼容 CDATA、转义链接和 content:encoded 正文。
    rows = parse_feed(data, source, base)
    for row in rows:
        row["source_type"] = "wechat"
        row["feed_url"] = base
        row["category"] = source.get("category", "")
    return rows


def load_sources(path: Path) -> tuple[list[dict], list[dict], list[dict]]:
    """读取并验证用户选择的 JSON 配置；配置错误时在联网前报错。"""
    config = json.loads(path.read_text(encoding="utf-8"))
    allowed_groups = ("rss", "url", "wechat")
    if not isinstance(config, dict) or set(config) - set(allowed_groups):
        raise ValueError("配置必须是只包含 rss、url、wechat 分组的 JSON 对象")
    groups = []
    for kind in allowed_groups:
        entries = config.get(kind, [])
        if not isinstance(entries, list):
            raise ValueError(f"{kind} 分组必须是列表")
        selected = []
        for item in entries:
            if not isinstance(item, dict):
                raise ValueError(f"{kind} 分组中的来源必须是对象")
            # 禁用的候选项不发起请求；开关必须是真正的布尔值，避免字符串误启用。
            enabled = item.get("enabled", True)
            if not isinstance(enabled, bool):
                raise ValueError("enabled 必须为 true 或 false")
            if not enabled:
                continue
            for key in ("name", "url"):
                if not isinstance(item.get(key), str) or not item[key].strip():
                    raise ValueError(f"每个启用来源必须填写字符串 {key}")
            for key in ("category", "content_selector"):
                if key in item and not isinstance(item[key], str):
                    raise ValueError(f"{key} 必须是字符串")
            # 公司标记只能由维护来源的人显式填写，不根据来源名称猜测。
            if "ai_company" in item and (
                not isinstance(item["ai_company"], str) or not item["ai_company"].strip()
            ):
                raise ValueError("ai_company 必须是非空字符串")
            if "reference_id" in item and (
                not isinstance(item["reference_id"], str) or not item["reference_id"].strip()
            ):
                raise ValueError("reference_id 必须是非空字符串")
            if "max_articles" in item and (
                type(item["max_articles"]) is not int or not 1 <= item["max_articles"] <= 100
            ):
                raise ValueError("max_articles 必须是 1 到 100 的整数")
            normalize_url(item["url"])
            selected.append(item)
        groups.append(selected)
    return tuple(groups)


def collect(
    rss_sources: list[dict], url_sources: list[dict], wechat_sources: list[dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    """顺序采集并按链接去重；单个来源失败不影响其余来源，返回条目和错误。"""
    articles, errors = [], []
    seen: dict[str, dict] = {}
    sources = [("rss", item) for item in rss_sources] + [("url", item) for item in url_sources]
    sources += [("wechat", item) for item in (wechat_sources or [])]
    with create_session() as session:
        for index, (kind, source) in enumerate(sources):
            if index:
                time.sleep(1)  # 来源间留出间隔，避免连续高频访问。
            try:
                if not source.get("name") or not source.get("url"):
                    raise ValueError("每个来源都必须填写 name 和 url")
                data, final_url, encoding = fetch(session, source["url"])
                if kind == "wechat":
                    rows = parse_wechat_feed(data, source, final_url)
                elif kind == "rss":
                    rows = parse_feed(data, source, final_url)
                else:
                    rows = parse_page(data, source, final_url, encoding)
                # 已知发布时间的条目优先取最新；无发布时间的条目保留原相对顺序。
                if kind in {"rss", "wechat"}:
                    rows.sort(key=lambda item: item["published_at"] or "", reverse=True)
                # 仅收录前 N 条，控制快照大小和后续评分次数。
                rows = rows[:source.get("max_articles", len(rows))]
                for row in rows:
                    if row["url"] not in seen:
                        row["collected_at"] = datetime.now(timezone.utc).isoformat()
                        # 网页列表要区分 RSS、公众号和单篇网页来源。
                        row["source_type"] = kind
                        # 来源分类与参考编号是采集元数据，不与模型生成的文章分类混用。
                        if source.get("category"):
                            row["source_category"] = source["category"]
                        if source.get("reference_id"):
                            row["reference_id"] = source["reference_id"]
                        # 保存配置中的订阅地址，供排序阶段精确匹配参考目录的来源。
                        row["source_feed_url"] = source["url"]
                        row["source_feed_urls"] = [source["url"]]
                        # 第三方 RSS 的文章链接未必是官网，保留人工确认的公司身份。
                        if source.get("ai_company"):
                            row["ai_company"] = source["ai_company"].strip()
                        seen[row["url"]] = row
                        articles.append(row)
                    else:
                        # 同一链接可先由转载源收录；保留后续订阅地址与官方身份。
                        original = seen[row["url"]]
                        if source["url"] not in original["source_feed_urls"]:
                            original["source_feed_urls"].append(source["url"])
                        if source.get("ai_company") and not original.get("ai_company"):
                            original["ai_company"] = source["ai_company"].strip()
                LOGGER.info("来源 %s 解析到 %d 条资讯", source["name"], len(rows))
            except Exception as exc:
                # 来源适配存在差异，在此隔离解析异常；错误清单让失败可追踪。
                name = source.get("name", "未命名来源")
                errors.append({"source": name, "error": str(exc)})
                LOGGER.warning("来源 %s 采集失败：%s", name, exc)
    return articles, errors


def save_result(
    path: Path, articles: list[dict], errors: list[dict], ranking: dict | None = None,
) -> dict:
    """原子写入本次快照，并返回同一份数据供 SQLite 入库。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"collected_at": datetime.now(timezone.utc).isoformat(),
               "articles": articles, "errors": errors}
    if ranking is not None:
        payload["ranking"] = ranking
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    return payload


def main() -> int:
    """默认从配置采集并评分；来源或模型失败时返回非零状态码。"""
    parser = argparse.ArgumentParser(description="spiderAI RSS、微信公众号与静态网页采集器")
    parser.add_argument("--output", type=Path, help="JSON 输出路径；指定已有文件将覆盖")
    # 无参数时使用项目配置，单次采集即可完成抓取、评分和入库。
    parser.add_argument("--sources", type=Path, default=ROOT / "config" / "sources.json",
                        help="来源 JSON 配置；默认使用 config/sources.json")
    # 默认评分；保留旧开关兼容已有命令，显式跳过时不读取模型密钥。
    scoring = parser.add_mutually_exclusive_group()
    scoring.add_argument("--score", dest="score", action="store_true", default=True,
                         help="采集后调用配置的模型评分；默认已启用，保留旧命令兼容")
    scoring.add_argument("--no-score", dest="score", action="store_false",
                         help="仅采集并入库，本次不调用模型")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s：%(message)s")
    try:
        rss, urls, wechat = load_sources(args.sources)
    except (OSError, ValueError) as exc:
        parser.error(f"无法读取来源配置：{exc}")
    if not rss and not urls and not wechat:
        LOGGER.info("来源配置中没有已启用条目；请启用来源或用 --sources 指定其他配置。")
        return 0
    client = None
    if args.score:
        # 联网采集前校验密钥，避免采集完成后才发现无法评分。
        from app.llm import AIClient, AIError
        try:
            client = AIClient.from_env()
        except AIError as exc:
            parser.error(str(exc))
    articles, errors = collect(rss, urls, wechat)
    ranking = None
    failed_scores = 0
    if client is not None and articles:
        from app.rank import rank_snapshot
        ranked, failed_scores = rank_snapshot({"articles": articles}, client)
        articles, ranking = ranked["articles"], ranked["ranking"]
    # JSON 暂存本次采集以便重试和评分；SQLite 负责跨次去重和网页历史查询。
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = args.output or ROOT / "data" / f"articles-{stamp}.json"
    payload = save_result(output, articles, errors, ranking)
    LOGGER.info("保存 %d 条资讯，%d 个来源失败：%s", len(articles), len(errors), output)
    from app.db import cleanup_if_due, save_snapshot
    from app.snapshots import cleanup_expired_snapshots
    try:
        inserted, updated = save_snapshot(payload)
        # 本地服务未运行时，采集命令也负责补做已到期的七天清理。
        removed = cleanup_if_due()
    except (OSError, ValueError, sqlite3.Error) as exc:
        LOGGER.error("SQLite 入库失败，JSON 快照仍可用于重试导入：%s", exc)
        return 1
    LOGGER.info("SQLite 归档新增 %d 条，更新 %d 条", inserted, updated)
    if removed:
        LOGGER.info("已清理 %d 条超过七天的未收藏资讯", removed)
    # 入库成功后才移除三天前的 JSON，避免在数据库故障时提前失去旧快照。
    expired = cleanup_expired_snapshots()
    if expired:
        LOGGER.info("已清理 %d 个超过三天的 JSON 快照", expired)
    if ranking is not None:
        LOGGER.info("完成 %d 条评分，%d 条评分失败", ranking["scored"], failed_scores)
        for article in articles[:10]:
            LOGGER.info("%s 分（来源加分 %s）：%s",
                        article["rank_score"] if article["rank_score"] is not None else "未评分",
                        article["source_bonus"], article["title"])
    return 1 if errors or failed_scores else 0


if __name__ == "__main__":
    # 导入模块时不触发采集，便于后端复用和离线测试。
    raise SystemExit(main())
