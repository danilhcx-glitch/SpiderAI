"""验证三天快照清理只影响数据目录内过期的有效快照。"""

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest

from app.snapshots import cleanup_expired_snapshots


class SnapshotCleanupTests(unittest.TestCase):
    """覆盖到期判断及非快照文件的保护条件。"""

    def test_expired_snapshots_only(self):
        """只删超过三天的快照，保留新快照、普通 JSON 和目录外文件。"""
        now = datetime(2026, 9, 27, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "data"
            data.mkdir()
            payload = {"collected_at": now.isoformat(), "articles": []}
            expired = data / "articles-old.json"
            fresh = data / "articles-new.json"
            other = data / "settings.json"
            outside = root / "articles-outside.json"
            for path in (expired, fresh, outside):
                path.write_text(json.dumps(payload), encoding="utf-8")
            other.write_text('{"theme": "dark"}', encoding="utf-8")
            # 以最后写入时间计算期限，明确验证三天边界。
            expired_at = (now - timedelta(days=3, seconds=1)).timestamp()
            fresh_at = (now - timedelta(days=3)).timestamp()
            other_at = (now - timedelta(days=4)).timestamp()
            os.utime(expired, (expired_at, expired_at))
            os.utime(fresh, (fresh_at, fresh_at))
            os.utime(other, (other_at, other_at))
            self.assertEqual(cleanup_expired_snapshots(data, now), 1)
            self.assertFalse(expired.exists())
            self.assertTrue(fresh.exists())
            self.assertTrue(other.exists())
            self.assertTrue(outside.exists())

    def test_symlink_is_not_removed(self):
        """即使链接指向过期快照，也不得清理符号链接或其目标。"""
        now = datetime(2026, 9, 27, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "data"
            data.mkdir()
            target = root / "snapshot.json"
            target.write_text(json.dumps({"collected_at": now.isoformat(), "articles": []}), encoding="utf-8")
            old_time = (now - timedelta(days=4)).timestamp()
            os.utime(target, (old_time, old_time))
            link = data / "snapshot-link.json"
            link.symlink_to(target)
            self.assertEqual(cleanup_expired_snapshots(data, now), 0)
            self.assertTrue(link.is_symlink())
            self.assertTrue(target.exists())


if __name__ == "__main__":
    # 支持直接运行这个测试文件。
    unittest.main()
