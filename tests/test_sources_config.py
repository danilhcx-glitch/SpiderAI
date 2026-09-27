"""核对实际采集配置覆盖候选订阅源，同时保持首批采集规模可控。"""

import json
from pathlib import Path
import unittest

import collecter


ROOT = Path(collecter.__file__).resolve().parent


class SourceConfigTests(unittest.TestCase):
    """验证参考目录映射、启用数量和单源收录上限。"""

    def test_all_supported_feeds_are_configured(self):
        """所有可由当前解析器处理的候选订阅源都应进入配置且地址一致。"""
        catalog = json.loads((ROOT / "docs/reference-sources.json").read_text(encoding="utf-8"))
        config = json.loads((ROOT / "config/sources.json").read_text(encoding="utf-8"))
        supported = {row["id"]: row for row in catalog["sources"] if row["kind"] in {
            "RSS", "YouTube RSS", "示例 RSS", "微信公众号 RSS",
        }}
        configured = {row["reference_id"]: row for group in config.values() for row in group}
        self.assertEqual(len(supported), 129)
        self.assertEqual(set(configured), set(supported))
        for source_id, row in configured.items():
            with self.subTest(source_id=source_id):
                self.assertEqual(row["url"], supported[source_id]["url"])
                self.assertEqual(row["name"], supported[source_id]["name"])
                self.assertEqual(row["category"], supported[source_id]["category"])
                self.assertEqual(row["max_articles"], 3)
        self.assertEqual(len(config["rss"]), 76)
        self.assertEqual(len(config["wechat"]), 53)
        self.assertEqual(config["url"], [])

    def test_only_small_first_batch_is_enabled(self):
        """首批仅五个重点账号会发请求，其余已登记来源保持关闭。"""
        config = json.loads((ROOT / "config/sources.json").read_text(encoding="utf-8"))
        active = {row["reference_id"] for group in config.values()
                  for row in group if row["enabled"]}
        self.assertEqual(active, {"S023", "S024", "S045", "S127", "S128"})
        rss, urls, wechat = collecter.load_sources(ROOT / "config/sources.json")
        self.assertEqual(len(rss), 5)
        self.assertEqual((urls, wechat), ([], []))

    def test_invalid_limit_rejected_before_network(self):
        """条数上限不能是布尔值、零或超过约定的最大值。"""
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.json"
            for limit in (True, 0, 101, "3"):
                with self.subTest(limit=limit):
                    path.write_text(json.dumps({"rss": [{
                        "name": "示例", "url": "https://example.com/feed", "max_articles": limit,
                    }]}), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        collecter.load_sources(path)


if __name__ == "__main__":
    # 测试仅读取本地目录和配置，不访问候选网站。
    unittest.main()
