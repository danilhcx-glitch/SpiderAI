"""验证 SQLite 归档、收藏保护、定期清理和失败回滚。"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from app.db import (cleanup_if_due, import_favorites, list_favorites,
                    load_archive, remove_favorite, save_snapshot)
from app.web import to_frontend_data


class DatabaseTests(unittest.TestCase):
    """使用临时数据库检验采集快照到网页数据的完整路径。"""

    def test_cross_run_deduplication_and_archive(self):
        """重复链接只保留一篇，首次时间和旧评分不被后续无评分采集覆盖。"""
        now = datetime.now(timezone.utc).replace(microsecond=0)
        first = (now - timedelta(days=2)).isoformat()
        recent = (now - timedelta(hours=1)).isoformat()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "archive.sqlite3"
            older = {"collected_at": first, "articles": [
                {"title": "旧文章", "url": "https://example.com/a#section", "source": "示例",
                 "source_type": "rss", "published_at": None, "rank_score": 88,
                 "content": "测试正文" * 100_000},
            ], "errors": []}
            newer = {"collected_at": recent, "articles": [
                {"title": "更新标题", "url": "https://example.com/a", "source": "示例",
                 "source_type": "rss", "published_at": None},
                {"title": "新文章", "url": "https://example.com/b", "source": "示例",
                 "source_type": "rss", "published_at": recent},
            ], "errors": [{"source": "坏源", "error": "模拟失败"}]}
            self.assertEqual(save_snapshot(older, database), (1, 0))
            self.assertEqual(save_snapshot(newer, database), (1, 1))
            self.assertEqual(save_snapshot(newer, database), (0, 2))
            archive = load_archive(database, "7d", now)
            self.assertEqual(archive["archive_total"], 2)
            self.assertEqual(archive["errors"][0]["source"], "坏源")
            earlier = next(item for item in archive["articles"] if item["url"].endswith("/a"))
            self.assertEqual(earlier["first_seen_at"], first)
            self.assertEqual(earlier["last_seen_at"], recent)
            self.assertEqual(earlier["rank_score"], 88)
            # 列表查询不返回大段正文，防止页面刷新时占用与正文总量成正比的内存。
            self.assertNotIn("content", earlier)
            daily = to_frontend_data(load_archive(database, "24h", now), "24h", now)
            self.assertEqual([item["title"] for item in daily["items"]], ["新文章"])
            self.assertEqual(daily["archive_total"], 2)

    def test_invalid_snapshot_does_not_change_database(self):
        """结构错误的快照在写入前被拒绝，现有文章保持可读取。"""
        now = datetime.now(timezone.utc).isoformat()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "archive.sqlite3"
            save_snapshot({"collected_at": now, "articles": [
                {"title": "正常", "url": "https://example.com/ok"},
            ]}, database)
            with self.assertRaises(ValueError):
                save_snapshot({"articles": [{"title": "新增", "url": "https://example.com/new"}, None]},
                              database)
            self.assertEqual(load_archive(database, "7d")["archive_total"], 1)

    def test_seven_day_cleanup_preserves_favorites(self):
        """七天周期到期后只删超龄未收藏文章，旧收藏迁移前禁止清理。"""
        now = datetime.now(timezone.utc).replace(microsecond=0)
        old = (now - timedelta(days=8)).isoformat()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "archive.sqlite3"
            save_snapshot({"collected_at": old, "articles": [
                {"title": "保留", "url": "https://example.com/kept"},
                {"title": "清理", "url": "https://example.com/deleted"},
            ]}, database)
            self.assertEqual(cleanup_if_due(database, now), 0)
            self.assertEqual(load_archive(database, "7d", now)["archive_total"], 2)
            imported = import_favorites({"https://example.com/kept": {
                "title": "保留", "timestamp": int(now.timestamp() * 1000),
            }}, database)
            self.assertIn("https://example.com/kept", imported)
            self.assertEqual(cleanup_if_due(database, now + timedelta(days=6)), 0)
            # 首次迁移后新增的文章尚未满七天，第一次到期清理仍要保留。
            recent = (now + timedelta(days=6)).isoformat()
            save_snapshot({"collected_at": recent, "articles": [
                {"title": "近期", "url": "https://example.com/recent"},
            ]}, database)
            self.assertEqual(cleanup_if_due(database, now + timedelta(days=8)), 1)
            self.assertEqual(load_archive(database, "7d", now + timedelta(days=8))["archive_total"], 2)
            self.assertIn("https://example.com/kept", list_favorites(database))
            self.assertEqual(cleanup_if_due(database, now + timedelta(days=9)), 0)
            remove_favorite("https://example.com/kept", database)
            self.assertEqual(cleanup_if_due(database, now + timedelta(days=16)), 2)
            self.assertEqual(load_archive(database, "7d", now + timedelta(days=16))["archive_total"], 0)

    def test_bad_favorite_import_does_not_enable_cleanup(self):
        """旧收藏格式错误时保留文章，等待用户修复迁移数据。"""
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "archive.sqlite3"
            save_snapshot({"collected_at": (now - timedelta(days=9)).isoformat(), "articles": [
                {"title": "待保护", "url": "https://example.com/a"},
            ]}, database)
            with self.assertRaises(ValueError):
                import_favorites({"https://example.com/a": "错误格式"}, database)
            self.assertEqual(cleanup_if_due(database, now + timedelta(days=20)), 0)
            self.assertEqual(load_archive(database, "7d", now)["archive_total"], 1)


if __name__ == "__main__":
    unittest.main()
