"""管理 SQLite 文章归档、收藏、快照导入和定期清理。"""

from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
from pathlib import Path
import sqlite3
from urllib.parse import urldefrag, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "spiderai.sqlite3"
SCHEMA = ROOT / "migrations" / "001_initial.sql"
LOGGER = logging.getLogger("spiderAI.db")
CLEANUP_INTERVAL = timedelta(days=7)
ARTICLE_RETENTION = timedelta(days=7)


def _utc(value: object) -> str | None:
    """将带时区的时间统一转为 UTC；未知时间保留为空。"""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc).isoformat() if parsed.tzinfo else None


def _article_url(value: object) -> str | None:
    """仅归档可安全打开的 HTTP(S) 原文链接，并去掉页面片段。"""
    if not isinstance(value, str):
        return None
    url = urldefrag(value.strip())[0]
    try:
        parts = urlsplit(url)
        hostname = parts.hostname
    except ValueError:
        return None
    if parts.scheme not in {"http", "https"} or not hostname or parts.username or parts.password:
        return None
    return url


def connect(path: Path = DEFAULT_DB) -> sqlite3.Connection:
    """打开本地库并初始化结构；每次调用均由调用方关闭连接。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    # WAL 允许网页读取时采集器写入；数据库及伴随文件均位于被忽略的 data 目录。
    connection.execute("PRAGMA journal_mode = WAL")
    connection.executescript(SCHEMA.read_text(encoding="utf-8"))
    return connection


def save_snapshot(payload: dict, path: Path = DEFAULT_DB) -> tuple[int, int]:
    """原子导入快照，按链接去重并保留文章的首次发现时间。"""
    if not isinstance(payload, dict) or not isinstance(payload.get("articles"), list):
        raise ValueError("快照必须包含 articles 列表")
    if not isinstance(payload.get("errors", []), list):
        raise ValueError("快照的 errors 必须是列表")
    collected_at = _utc(payload.get("collected_at")) or datetime.now(timezone.utc).isoformat()
    rows = []
    for article in payload["articles"]:
        if not isinstance(article, dict):
            raise ValueError("articles 中的每项都必须是对象")
        url = _article_url(article.get("url"))
        title = article.get("title")
        if not url or not isinstance(title, str) or not title.strip():
            continue
        seen_at = _utc(article.get("collected_at")) or collected_at
        published_at = _utc(article.get("published_at"))
        source = article.get("source") if isinstance(article.get("source"), str) else ""
        source_type = article.get("source_type")
        if source_type not in {"rss", "wechat", "url"}:
            source_type = "rss" if article.get("source_feed_url") else "url"
        score = article.get("rank_score")
        score = score if type(score) in {int, float} else None
        normalized = {**article, "url": url, "collected_at": seen_at,
                      "published_at": published_at, "source_type": source_type}
        rows.append((url, title.strip(), source.strip() or "未知来源", source_type,
                     published_at, seen_at, published_at or seen_at, score,
                     json.dumps(normalized, ensure_ascii=False)))
    # 哈希使用完整快照内容，重复导入同一文件不会累积虚假的采集批次。
    snapshot_hash = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    inserted = updated = 0
    with closing(connect(path)) as connection:
        with connection:
            for url, title, source, kind, published, seen, effective, score, article_json in rows:
                existing = connection.execute(
                    "SELECT first_seen_at, last_seen_at, published_at, rank_score FROM articles WHERE url = ?",
                    (url,),
                ).fetchone()
                if existing is None:
                    connection.execute(
                        """INSERT INTO articles
                           (url, title, source, source_type, published_at, first_seen_at,
                            last_seen_at, effective_at, rank_score, payload_json)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (url, title, source, kind, published, seen, seen, effective, score, article_json),
                    )
                    inserted += 1
                else:
                    # 旧评分不会被未评分的新快照抹掉；同链接的阅读历史基于稳定 URL。
                    first = min(existing["first_seen_at"], seen)
                    last = max(existing["last_seen_at"], seen)
                    published = published or existing["published_at"]
                    score = score if score is not None else existing["rank_score"]
                    connection.execute(
                        """UPDATE articles SET title = ?, source = ?, source_type = ?,
                           published_at = ?, first_seen_at = ?, last_seen_at = ?,
                           effective_at = ?, rank_score = ?, payload_json = ? WHERE url = ?""",
                        (title, source, kind, published, first, last, published or first,
                         score, article_json, url),
                    )
                    updated += 1
            connection.execute(
                "INSERT OR IGNORE INTO collection_runs (snapshot_hash, collected_at, errors_json) VALUES (?, ?, ?)",
                (snapshot_hash, collected_at, json.dumps(payload.get("errors", []), ensure_ascii=False)),
            )
    return inserted, updated


def load_archive(path: Path = DEFAULT_DB, range_name: str = "24h",
                 now: datetime | None = None) -> dict:
    """只读取页面所需的文章字段，附带归档总量和最近一次采集错误。"""
    if range_name not in {"24h", "7d"}:
        raise ValueError("时间范围必须是 24h 或 7d")
    if not path.is_file():
        return {"collected_at": None, "articles": [], "errors": [], "archive_total": 0}
    current = now or datetime.now(timezone.utc)
    hours = 24 if range_name == "24h" else 168
    cutoff = (current - timedelta(hours=hours)).astimezone(timezone.utc).isoformat()
    with closing(connect(path)) as connection:
        # 正文保存在 payload_json，但列表页不读取它，避免文章积累后放大内存占用。
        # 已评分资讯延续原有重要性排序，同分或未评分资讯按发布时间排列。
        rows = connection.execute(
            """SELECT url, title, source, source_type, published_at, first_seen_at,
                      last_seen_at, rank_score FROM articles WHERE effective_at >= ?
               ORDER BY (rank_score IS NULL), rank_score DESC, effective_at DESC""",
            (cutoff,),
        ).fetchall()
        total = connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        latest = connection.execute(
            "SELECT collected_at, errors_json FROM collection_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    # 直接使用归档字段，避免把完整正文反序列化后再丢弃。
    articles = [dict(row) for row in rows]
    return {"collected_at": latest["collected_at"] if latest else None,
            "articles": articles, "errors": json.loads(latest["errors_json"]) if latest else [],
            "archive_total": total}


def list_favorites(path: Path = DEFAULT_DB) -> dict[str, dict]:
    """读取 SQLite 中的全部收藏，保持前端现有的链接到信息映射格式。"""
    with closing(connect(path)) as connection:
        rows = connection.execute(
            "SELECT url, title, timestamp_ms FROM favorites ORDER BY timestamp_ms DESC"
        ).fetchall()
    return {row["url"]: {"title": row["title"], "timestamp": row["timestamp_ms"]}
            for row in rows}


def _favorite_values(url: object, title: object, timestamp: object = None) -> tuple[str, str, int]:
    """校验收藏输入，阻止无效链接或异常大的字段进入本地库。"""
    normalized = _article_url(url)
    if normalized is None or len(normalized) > 4096:
        raise ValueError("收藏链接必须是有效的 HTTP(S) 地址")
    if not isinstance(title, str) or len(title) > 500:
        raise ValueError("收藏标题必须是不超过 500 字的字符串")
    if timestamp is None:
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    if type(timestamp) is not int or not 0 < timestamp < 10**14:
        raise ValueError("收藏时间戳无效")
    return normalized, title, timestamp


def set_favorite(url: str, title: str, path: Path = DEFAULT_DB) -> dict:
    """新增或更新一条收藏，并返回前端需要的标题和时间戳。"""
    normalized, title, timestamp = _favorite_values(url, title)
    with closing(connect(path)) as connection:
        with connection:
            connection.execute(
                """INSERT INTO favorites (url, title, timestamp_ms) VALUES (?, ?, ?)
                   ON CONFLICT(url) DO UPDATE SET title = excluded.title""",
                (normalized, title, timestamp),
            )
            row = connection.execute(
                "SELECT title, timestamp_ms FROM favorites WHERE url = ?", (normalized,)
            ).fetchone()
    return {"url": normalized, "title": row["title"], "timestamp": row["timestamp_ms"]}


def remove_favorite(url: str, path: Path = DEFAULT_DB) -> None:
    """按链接取消收藏；不存在的链接视为已取消。"""
    normalized = _article_url(url)
    if normalized is None:
        raise ValueError("收藏链接无效")
    with closing(connect(path)) as connection:
        with connection:
            connection.execute("DELETE FROM favorites WHERE url = ?", (normalized,))


def clear_favorites(path: Path = DEFAULT_DB) -> None:
    """清空收藏表；文章按下次到期清理规则处理。"""
    with closing(connect(path)) as connection:
        with connection:
            connection.execute("DELETE FROM favorites")


def import_favorites(favorites: dict, path: Path = DEFAULT_DB) -> dict[str, dict]:
    """一次性迁移浏览器旧收藏；成功后允许数据库执行自动清理。"""
    if not isinstance(favorites, dict) or len(favorites) > 500:
        raise ValueError("旧收藏必须是不超过 500 条的对象")
    valid = []
    for url, info in favorites.items():
        # 坏记录应阻止启用清理，避免把本该保护的旧收藏文章误删。
        if not isinstance(info, dict):
            raise ValueError("旧收藏记录格式无效")
        valid.append(_favorite_values(url, info.get("title", ""), info.get("timestamp")))
    with closing(connect(path)) as connection:
        with connection:
            connection.executemany(
                "INSERT OR IGNORE INTO favorites (url, title, timestamp_ms) VALUES (?, ?, ?)",
                valid,
            )
            connection.execute(
                "INSERT OR REPLACE INTO maintenance (key, value) VALUES ('favorites_ready', '1')"
            )
            # 首次迁移后再等待一个完整周期，留出其他浏览器同步旧收藏的时间。
            connection.execute(
                "INSERT OR IGNORE INTO maintenance (key, value) VALUES ('last_cleanup_at', ?)",
                (datetime.now(timezone.utc).isoformat(),),
            )
    return list_favorites(path)


def cleanup_if_due(path: Path = DEFAULT_DB, now: datetime | None = None) -> int:
    """每隔七天清理首次收录超过七天的未收藏文章；返回删除数量。"""
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = (current - ARTICLE_RETENTION).isoformat()
    deleted = 0
    with closing(connect(path)) as connection:
        with connection:
            state = dict(connection.execute("SELECT key, value FROM maintenance").fetchall())
            # 旧收藏未从浏览器迁移前不得清理，否则无法辨认需要保护的文章。
            if state.get("favorites_ready") != "1":
                return 0
            previous = _utc(state.get("last_cleanup_at"))
            if previous and current - datetime.fromisoformat(previous) < CLEANUP_INTERVAL:
                return 0
            cursor = connection.execute(
                """DELETE FROM articles WHERE first_seen_at < ?
                   AND NOT EXISTS (SELECT 1 FROM favorites WHERE favorites.url = articles.url)""",
                (cutoff,),
            )
            deleted = cursor.rowcount
            connection.execute(
                "INSERT OR REPLACE INTO maintenance (key, value) VALUES ('last_cleanup_at', ?)",
                (current.isoformat(),),
            )
        if deleted:
            # 删除后压缩数据库文件，实际释放磁盘；繁忙时保留可复用空页。
            try:
                connection.execute("VACUUM")
            except sqlite3.OperationalError as exc:
                LOGGER.warning("文章已清理，但数据库压缩暂未完成：%s", exc)
    return deleted


def main() -> None:
    """提供本地库初始化和旧 JSON 快照批量导入命令。"""
    parser = argparse.ArgumentParser(description="管理 SpiderAI 本地 SQLite 归档")
    parser.add_argument("command", choices=("init", "import"))
    parser.add_argument("snapshots", nargs="*", type=Path, help="待导入的 JSON 快照")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="数据库文件路径")
    args = parser.parse_args()
    if args.command == "import" and not args.snapshots:
        parser.error("import 需要至少一个 JSON 快照路径")
    if args.command == "init" and args.snapshots:
        parser.error("init 不接受快照路径")
    with closing(connect(args.db)):
        pass
    for snapshot in args.snapshots:
        try:
            payload = json.loads(snapshot.read_text(encoding="utf-8"))
            inserted, updated = save_snapshot(payload, args.db)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, sqlite3.Error) as exc:
            parser.error(f"导入 {snapshot} 失败：{exc}")
        print(f"{snapshot}：新增 {inserted}，更新 {updated}")
    # 手动导入历史快照后也检查清理周期，避免过期文章再次长期留存。
    removed = cleanup_if_due(args.db)
    if removed:
        print(f"自动清理 {removed} 条超过七天的未收藏资讯")
    print(f"SQLite 数据库：{args.db}")


if __name__ == "__main__":
    main()
