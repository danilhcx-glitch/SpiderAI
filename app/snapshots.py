"""清理本地数据目录中过期的采集与评分 JSON 快照。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path


DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
RETENTION = timedelta(days=3)
LOGGER = logging.getLogger("spiderAI.snapshots")


def cleanup_expired_snapshots(data_root: Path = DATA_ROOT, now: datetime | None = None) -> int:
    """删除数据目录内最后写入已超过三天的有效快照，返回删除数量。"""
    cutoff = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).timestamp() - RETENTION.total_seconds()
    deleted = 0
    for path in data_root.glob("*.json"):
        # 仅处理本层普通文件；配置文件、符号链接和其他目录不属于快照清理范围。
        if path.is_symlink() or not path.is_file():
            continue
        try:
            original = path.stat()
            if original.st_mtime >= cutoff:
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            # 识别采集器和评分器的快照结构，避免误删 data 中的其他 JSON 文件。
            if not (isinstance(payload, dict) and isinstance(payload.get("collected_at"), str)
                    and isinstance(payload.get("articles"), list)):
                continue
            # 并发采集可能覆盖同名文件；删除前确认它仍是刚才检查的旧文件。
            latest = path.stat()
            if (latest.st_ino, latest.st_mtime_ns) != (original.st_ino, original.st_mtime_ns):
                continue
            path.unlink()
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            LOGGER.warning("无法检查或清理快照 %s：%s", path, exc)
            continue
        deleted += 1
    return deleted
