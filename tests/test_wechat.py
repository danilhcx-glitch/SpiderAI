"""离线验证微信公众号订阅、配置筛选与命令行集成。"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collecter


# 模拟第三方公众号 RSS，覆盖频道更新时间、CDATA 和带查询参数的微信链接。
FEED = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel><title>微信公众号-测试号</title>
<lastBuildDate>Sat, 26 Sep 2026 10:00:00 GMT</lastBuildDate>
<item><title><![CDATA[模型 & 新进展]]></title>
<link>https://mp.weixin.qq.com/s?__biz=test&amp;mid=1&amp;idx=1&amp;sn=abc</link>
<description><![CDATA[<p>文章摘要</p>]]></description>
<content:encoded><![CDATA[<p>完整正文</p><script>不保留</script>]]></content:encoded>
<pubDate>Fri, 25 Sep 2026 08:00:00 +0800</pubDate></item>
<item><title>未知发布时间</title><link>https://mp.weixin.qq.com/s/unknown</link></item>
</channel></rss>'''.encode("utf-8")
SOURCE = {"name": "测试号", "url": "https://example.com/wechat.xml", "category": "AI"}


class WechatTests(unittest.TestCase):
    """验证公众号来源不会混淆时间、链接和数据来源，也不会默认联网。"""

    def test_content_metadata_and_date(self):
        """CDATA、正文、公众号分类和逐篇发布时间应正确保留。"""
        row = collecter.parse_wechat_feed(FEED, SOURCE, SOURCE["url"])[0]
        self.assertEqual(row["title"], "模型 & 新进展")
        self.assertEqual(row["summary"], "文章摘要")
        self.assertEqual(row["content"], "完整正文")
        self.assertIn("__biz=test&mid=1&idx=1&sn=abc", row["url"])
        self.assertEqual(row["published_at"], "2026-09-25T00:00:00+00:00")
        self.assertEqual(row["source_type"], "wechat")
        self.assertEqual(row["category"], "AI")
        self.assertEqual(row["feed_url"], SOURCE["url"])

    def test_channel_update_is_not_article_publication(self):
        """未知文章时间必须留空，不能借用频道 lastBuildDate。"""
        rows = collecter.parse_wechat_feed(FEED, SOURCE, SOURCE["url"])
        self.assertIsNone(rows[1]["published_at"])

    @patch("collecter.time.sleep")
    @patch("collecter.fetch")
    def test_failure_isolation_and_deduplication(self, fetch, sleep):
        """公众号请求失败不影响下一个来源，同一原文重复出现时只保存一次。"""
        fetch.side_effect = [ValueError("模拟不可用"), (FEED, SOURCE["url"], None),
                             (FEED, SOURCE["url"], None)]
        rows, errors = collecter.collect([], [], [SOURCE, SOURCE, SOURCE])
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(errors), 1)
        self.assertTrue(all(row["source_type"] == "wechat" for row in rows))

    def test_selected_config(self):
        """仅加载已选择来源，禁用占位项不会被当成有效请求。"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.json"
            path.write_text(json.dumps({"wechat": [SOURCE, {"enabled": False}]}))
            self.assertEqual(collecter.load_sources(path), ([], [], [SOURCE]))

    def test_reject_bad_config(self):
        """错误分组、类型、URL 和字符串开关应在发起请求前被拒绝。"""
        invalid_configs = [[], {"wecaht": []}, {"wechat": {}}, {"wechat": [None]},
                           {"wechat": [{**SOURCE, "enabled": "false"}]},
                           {"wechat": [{**SOURCE, "url": "file:///tmp/test"}]},
                           {"wechat": [{**SOURCE, "category": []}]}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.json"
            for config in invalid_configs:
                with self.subTest(config=config):
                    path.write_text(json.dumps(config))
                    with self.assertRaises(ValueError):
                        collecter.load_sources(path)

    @patch("collecter.fetch")
    def test_empty_configuration_never_fetches(self, fetch):
        """默认配置与显式配置都为空时，不发起网络采集。"""
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config" / "sources.json"
            config.parent.mkdir()
            config.write_text('{"rss": [], "url": [], "wechat": []}', encoding="utf-8")
            for argv in [["collecter.py"], ["collecter.py", "--sources", str(config)]]:
                # 将默认配置根目录指向临时文件，防止测试访问真实来源。
                with patch("collecter.ROOT", Path(directory)), patch("sys.argv", argv):
                    self.assertEqual(collecter.main(), 0)
        fetch.assert_not_called()

    @patch("collecter.fetch", return_value=(FEED, SOURCE["url"], None))
    def test_cli_writes_wechat_snapshot(self, fetch):
        """命令行配置应走完整采集路径并输出公众号元数据。"""
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "sources.json"
            output = Path(directory) / "result.json"
            config.write_text(json.dumps({"wechat": [SOURCE]}))
            # 测试采集接口时隔离默认 SQLite 文件。
            with patch("app.db.save_snapshot", return_value=(0, 0)), patch("app.db.cleanup_if_due", return_value=0), patch("sys.argv", ["collecter.py", "--sources", str(config),
                                    "--output", str(output), "--no-score"]):
                self.assertEqual(collecter.main(), 0)
            payload = json.loads(output.read_text())
            self.assertEqual(len(payload["articles"]), 2)
            self.assertEqual(payload["articles"][0]["source_type"], "wechat")
            self.assertEqual(payload["errors"], [])
            fetch.assert_called_once()


if __name__ == "__main__":
    # 支持单独运行本文件，所有网络响应均由本地样本替代。
    unittest.main()
