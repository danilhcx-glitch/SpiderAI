"""为 React 前端提供本地静态文件、资讯查询和收藏接口。"""

from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import sqlite3
from threading import Event, Thread
from urllib.parse import parse_qs, urlsplit

from app.db import (cleanup_if_due, clear_favorites, connect, import_favorites,
                    list_favorites, load_archive, remove_favorite, set_favorite)
from app.snapshots import cleanup_expired_snapshots


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
DIST_ROOT = ROOT / "web" / "dist"
SITE_NAMES = {"rss": "RSS 订阅", "wechat": "微信公众号", "url": "网页文章"}


def load_snapshot(path: Path | None = None, data_root: Path = DATA_ROOT) -> dict:
    """读取指定或最新的有效采集快照；尚无数据时返回空快照。"""
    if path is not None:
        candidates = [path]
    else:
        # 默认只扫描 data 中的普通 JSON 文件，随后验证其文章结构。
        candidates = sorted(
            (item for item in data_root.glob("*.json") if item.is_file() and not item.is_symlink()),
            key=lambda item: item.stat().st_mtime_ns,
            reverse=True,
        )
    for candidate in candidates:
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            if path is not None:
                raise ValueError(f"无法读取快照：{candidate}") from None
            continue
        if isinstance(payload, dict) and isinstance(payload.get("articles"), list):
            if all(isinstance(article, dict) for article in payload["articles"]):
                return payload
        if path is not None:
            raise ValueError("快照必须包含 articles 对象列表")
    return {"collected_at": None, "articles": [], "errors": [], "empty": True}


def _parse_time(value: object) -> datetime | None:
    """只接受带时区的 ISO 时间，避免猜测原文发布时间所在时区。"""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else None


def _site_id(article: dict) -> str:
    """将采集器的来源类型映射为原版前端的平台筛选 ID。"""
    kind = article.get("source_type")
    if isinstance(kind, str) and kind in SITE_NAMES:
        return kind
    # 旧快照可能尚未保存 source_type，按已有订阅元数据保守归类。
    return "rss" if article.get("source_feed_url") else "url"


def to_frontend_data(snapshot: dict, range_name: str, now: datetime | None = None) -> dict:
    """把 SpiderAI articles 转为参考前端使用的 NewsData 结构。"""
    if range_name not in {"24h", "7d"}:
        raise ValueError("时间范围必须是 24h 或 7d")
    current = now or datetime.now(timezone.utc)
    hours = 24 if range_name == "24h" else 168
    cutoff = current - timedelta(hours=hours)
    items = []
    site_counts = {site_id: 0 for site_id in SITE_NAMES}
    sources: set[str] = set()
    for article in snapshot.get("articles", []):
        title, raw_url = article.get("title"), article.get("url")
        if not isinstance(title, str) or not title.strip() or not isinstance(raw_url, str):
            continue
        try:
            parts = urlsplit(raw_url)
            hostname = parts.hostname
        except ValueError:
            continue
        # 外部文章只能打开 HTTP(S)；不能把快照中的脚本 URL 注入链接。
        if parts.scheme not in {"http", "https"} or not hostname or parts.username or parts.password:
            continue
        published = _parse_time(article.get("published_at"))
        collected = (_parse_time(article.get("first_seen_at")) or
                     _parse_time(article.get("collected_at")) or
                     _parse_time(snapshot.get("collected_at")))
        last_seen = _parse_time(article.get("last_seen_at")) or collected
        effective = published or collected
        if effective is None or not cutoff <= effective <= current + timedelta(minutes=5):
            continue
        site_id = _site_id(article)
        source = article.get("source") if isinstance(article.get("source"), str) else "未知来源"
        source = source.strip() or "未知来源"
        site_counts[site_id] += 1
        sources.add(source)
        items.append({
            "id": hashlib.sha256(raw_url.encode("utf-8")).hexdigest()[:20],
            "site_id": site_id,
            "site_name": SITE_NAMES[site_id],
            "source": source,
            "title": title.strip(),
            "url": raw_url,
            "published_at": published.isoformat() if published else None,
            "first_seen_at": collected.isoformat() if collected else effective.isoformat(),
            "last_seen_at": last_seen.isoformat() if last_seen else effective.isoformat(),
            "title_original": title.strip(),
            "title_en": None,
            "title_zh": None,
            "title_bilingual": title.strip(),
            "rank_score": article.get("rank_score") if type(article.get("rank_score")) in {int, float} else None,
        })
    site_stats = [
        {"site_id": site_id, "site_name": SITE_NAMES[site_id], "count": count, "raw_count": count}
        for site_id, count in site_counts.items() if count
    ]
    return {
        "generated_at": snapshot.get("collected_at") or "",
        "window_hours": hours,
        "total_items": len(items),
        "total_items_ai_raw": len(items),
        "total_items_raw": len(items),
        "total_items_all_mode": len(items),
        "topic_filter": "none",
        "archive_total": snapshot.get("archive_total", len(snapshot.get("articles", []))),
        "site_count": len(site_stats),
        "source_count": len(sources),
        "site_stats": site_stats,
        "items": items,
    }


def source_status(snapshot: dict) -> dict:
    """向原版来源弹窗提供当前快照的来源错误信息。"""
    errors = snapshot.get("errors", [])
    failed = [item["source"] for item in errors if isinstance(item, dict) and isinstance(item.get("source"), str)]
    counts = {site_id: 0 for site_id in SITE_NAMES}
    for article in snapshot.get("articles", []):
        if isinstance(article, dict):
            counts[_site_id(article)] += 1
    sites = [
        {"site_id": site_id, "site_name": SITE_NAMES[site_id], "ok": True,
         "item_count": count, "duration_ms": 0, "error": None}
        for site_id, count in counts.items() if count
    ]
    return {"generated_at": snapshot.get("collected_at"), "sites": sites,
            "successful_sites": len(sites), "failed_sites": failed}


def source_groups(snapshot: dict, range_name: str = "24h", now: datetime | None = None) -> list[dict]:
    """按当前时间范围整理来源名，使弹窗和页面统计保持一致。"""
    groups: dict[str, dict[str, str]] = {site_id: {} for site_id in SITE_NAMES}
    for item in to_frontend_data(snapshot, range_name, now)["items"]:
        groups[item["site_id"]][item["source"]] = ""
    return [{"name": site_id, "feeds": [{"name": name, "url": url} for name, url in feeds.items()]}
            for site_id, feeds in groups.items() if feeds]


def make_handler(
    snapshot_path: Path | None = None,
    data_root: Path = DATA_ROOT,
    dist_root: Path = DIST_ROOT,
    db_path: Path | None = None,
):
    """构造读取 SQLite 归档或显式 JSON 快照的本地页面处理器。"""

    archive_path = db_path or data_root / "spiderai.sqlite3"

    class NewsHandler(BaseHTTPRequestHandler):
        """按固定规则提供 React 页面和兼容原版的数据。"""

        def do_GET(self) -> None:
            """处理前端请求，不允许访问构建目录之外的文件。"""
            parsed = urlsplit(self.path)
            route = parsed.path
            if route == "/api/favorites":
                try:
                    self._send_json({"favorites": list_favorites(archive_path)})
                except (OSError, sqlite3.Error):
                    self.send_error(500, "读取收藏失败")
                return
            if route in {"/api/news", "/data/source-status.json", "/data/opml-feeds.json"}:
                range_name = parse_qs(parsed.query).get("range", ["24h"])[0]
                if range_name not in {"24h", "7d"}:
                    self.send_error(400, "时间范围必须是 24h 或 7d")
                    return
                # --snapshot 用于检查单次 JSON；正常浏览从 SQLite 读取跨次归档。
                snapshot = (load_snapshot(snapshot_path, data_root) if snapshot_path else
                            load_archive(archive_path, range_name))
                if route == "/api/news":
                    try:
                        payload = to_frontend_data(snapshot, range_name)
                    except ValueError as exc:
                        self.send_error(400, str(exc))
                        return
                elif route == "/data/source-status.json":
                    payload = source_status(snapshot)
                else:
                    # 复用原版弹窗的数据格式，内容改为 SpiderAI 实际来源。
                    try:
                        payload = source_groups(snapshot, range_name)
                    except ValueError as exc:
                        self.send_error(400, str(exc))
                        return
                self._send_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
                return
            if route == "/":
                target = dist_root / "index.html"
            elif route.startswith("/assets/"):
                target = dist_root / route.lstrip("/")
            else:
                self.send_error(404, "页面不存在")
                return
            # resolve 后校验目录边界，拦截编码或符号链接导致的路径逃逸。
            if not target.resolve().is_relative_to(dist_root.resolve()):
                self.send_error(404, "页面不存在")
                return
            try:
                body = target.read_bytes()
            except OSError:
                self.send_error(503 if route == "/" else 404, "请先运行前端构建命令")
                return
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            self._send_bytes(body, content_type)

        def do_POST(self) -> None:
            """接收本地页面新增收藏或迁移旧浏览器收藏的 JSON 请求。"""
            route = urlsplit(self.path).path
            if route not in {"/api/favorites", "/api/favorites/import"}:
                self.send_error(404, "接口不存在")
                return
            try:
                payload = self._read_json()
                if route == "/api/favorites/import":
                    favorites = import_favorites(payload.get("favorites"), archive_path)
                    # 先完成旧收藏入库，再启用到期清理，避免误删原浏览器收藏。
                    cleanup_if_due(archive_path)
                    self._send_json({"favorites": favorites})
                else:
                    favorite = set_favorite(payload.get("url"), payload.get("title"), archive_path)
                    self._send_json(favorite)
            except ValueError as exc:
                self.send_error(400, str(exc))
            except (OSError, sqlite3.Error):
                self.send_error(500, "保存收藏失败")

        def do_DELETE(self) -> None:
            """取消一条收藏或按明确的全量路径清空收藏。"""
            parsed = urlsplit(self.path)
            try:
                if parsed.path == "/api/favorites":
                    values = parse_qs(parsed.query).get("url", [])
                    if len(values) != 1:
                        raise ValueError("必须指定一个收藏链接")
                    remove_favorite(values[0], archive_path)
                elif parsed.path == "/api/favorites/all":
                    clear_favorites(archive_path)
                else:
                    self.send_error(404, "接口不存在")
                    return
                self._send_json({"ok": True})
            except ValueError as exc:
                self.send_error(400, str(exc))
            except (OSError, sqlite3.Error):
                self.send_error(500, "删除收藏失败")

        def _read_json(self) -> dict:
            """只接受限长的 JSON 对象，阻止其他站点用简单表单写入本地接口。"""
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if content_type != "application/json":
                raise ValueError("请求必须使用 application/json")
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                raise ValueError("请求长度无效") from None
            if not 0 < length <= 2 * 1024 * 1024:
                raise ValueError("请求内容超过 2 MB 上限")
            try:
                payload = json.loads(self.rfile.read(length))
            except (UnicodeError, json.JSONDecodeError):
                raise ValueError("请求 JSON 无效") from None
            if not isinstance(payload, dict):
                raise ValueError("请求 JSON 必须是对象")
            return payload

        def _send_json(self, payload: dict) -> None:
            """发送禁用缓存的 JSON 响应。"""
            self._send_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                             "application/json; charset=utf-8")

        def _send_bytes(self, body: bytes, content_type: str) -> None:
            """发送明确长度及禁止缓存的响应，便于刷新后看到新入库文章。"""
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

    return NewsHandler


def _cleanup_loop(stopped: Event) -> None:
    """服务持续运行时每小时检查数据库与三天快照的清理条件。"""
    while not stopped.wait(3600):
        try:
            cleanup_if_due()
            cleanup_expired_snapshots()
        except (OSError, sqlite3.Error) as exc:
            print(f"自动清理失败：{exc}")


def main() -> None:
    """从命令行启动只监听本机的页面和 SQLite 查询接口。"""
    parser = argparse.ArgumentParser(description="运行 SpiderAI 资讯页面")
    parser.add_argument("--port", type=int, default=8765, help="本地端口，默认 8765")
    parser.add_argument("--snapshot", type=Path, help="指定一个采集或评分 JSON 快照")
    args = parser.parse_args()
    if args.snapshot is not None:
        # 在监听端口前报告用户指定文件的格式错误。
        try:
            load_snapshot(args.snapshot)
        except ValueError as exc:
            parser.error(str(exc))
    if not (DIST_ROOT / "index.html").is_file():
        parser.error("尚未构建前端：请先在 web 目录运行 npm install 和 npm run build")
    if args.snapshot is None:
        # 首次启动自动创建本地库；无需单独安装或启动数据库服务器。
        with closing(connect()):
            pass
        cleanup_if_due()
        # 服务重启时补做停机期间错过的 JSON 清理。
        cleanup_expired_snapshots()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(args.snapshot))
    stopped = Event()
    worker = Thread(target=_cleanup_loop, args=(stopped,), daemon=True)
    if args.snapshot is None:
        worker.start()
    print(f"SpiderAI 页面：http://127.0.0.1:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stopped.set()
        if worker.is_alive():
            worker.join(timeout=1)
        server.server_close()


if __name__ == "__main__":
    main()
