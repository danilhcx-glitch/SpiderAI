"""使用本地样本验证采集规则，不访问真实网站或调用模型。"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collecter


class CollectorTests(unittest.TestCase):
    """覆盖订阅解析、网页提取、故障隔离与文件输出。"""

    def test_rss(self):
        """RSS 相对链接应解析，HTML 摘要应转成纯文本，未知时间留空。"""
        data = b'<rss version="2.0"><channel><title>News</title><item><title>AI</title><link>/a#part</link><description>&lt;b&gt;News&lt;/b&gt;</description></item></channel></rss>'
        rows = collecter.parse_feed(data, {"name": "测试"}, "https://example.com/feed")
        self.assertEqual(rows[0]["url"], "https://example.com/a")
        self.assertEqual(rows[0]["summary"], "News")
        self.assertIsNone(rows[0]["published_at"])

    def test_atom(self):
        """Atom 的发布时间应转换为 UTC，脚本不能进入内容。"""
        data = b'<feed xmlns="http://www.w3.org/2005/Atom"><title>News</title><entry><title>AI</title><link href="https://example.com/a"/><published>2026-01-01T08:00:00+08:00</published><content type="html">&lt;p&gt;Text&lt;/p&gt;&lt;script&gt;bad&lt;/script&gt;</content></entry></feed>'
        row = collecter.parse_feed(data, {"name": "测试"}, "https://example.com")[0]
        self.assertEqual(row["published_at"], "2026-01-01T00:00:00+00:00")
        self.assertEqual(row["content"], "Text")

    def test_page(self):
        """静态文章应提取正文、去掉导航，并保留中文。"""
        data = '<html><meta charset="utf-8"><h1>标题</h1><article><nav>导航</nav><p>正文</p><script>bad</script></article></html>'.encode()
        row = collecter.parse_page(data, {"name": "测试"}, "https://example.com/a")[0]
        self.assertEqual(row["title"], "标题")
        self.assertEqual(row["content"], "正文")

    def test_missing_body(self):
        """找不到正文时应报错，不把整页导航当作文章。"""
        with self.assertRaises(ValueError):
            collecter.parse_page(b'<h1>Title</h1>', {"name": "测试"}, "https://example.com")

    def test_invalid_feed_and_url(self):
        """普通网页不能当作订阅源，脚本链接不能作为文章地址。"""
        with self.assertRaises(ValueError):
            collecter.parse_feed(b'<html>Error</html>', {"name": "测试"}, "https://example.com")
        with self.assertRaises(ValueError):
            collecter.normalize_url("javascript:alert(1)")

    @patch("collecter.time.sleep")
    @patch("collecter.fetch")
    def test_isolation_and_deduplication(self, fetch, sleep):
        """一个来源失败后继续处理，并合并重复文章链接。"""
        data = b'<rss version="2.0"><channel><item><title>AI</title><link>https://example.com/a</link></item></channel></rss>'
        fetch.side_effect = [ValueError("模拟失败"), (data, "https://example.com", None), (data, "https://example.com", None)]
        rows, errors = collecter.collect([
            {"name": str(i), "url": "https://example.com"} for i in range(3)
        ], [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("collected_at", rows[0])

    def test_save(self):
        """输出 JSON 应包含错误清单，写完不遗留临时文件。"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            collecter.save_result(path, [], [{"source": "测试", "error": "失败"}])
            result = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(result["errors"][0]["source"], "测试")
            self.assertEqual(list(Path(directory).iterdir()), [path])

    @patch("collecter.fetch")
    def test_source_article_limit(self, fetch):
        """单源条数上限应限制快照规模，避免后续模型处理大量旧条目。"""
        entries = "".join(
            f"<item><title>AI {index}</title><link>https://example.com/{index}</link></item>"
            for index in range(5)
        )
        feed = f'<rss version="2.0"><channel>{entries}</channel></rss>'.encode()
        fetch.return_value = (feed, "https://example.com/feed", None)
        rows, errors = collecter.collect([
            {"name": "示例", "url": "https://example.com/feed", "max_articles": 3},
        ], [])
        self.assertEqual(errors, [])
        self.assertEqual([row["title"] for row in rows], ["AI 0", "AI 1", "AI 2"])
        # 网页筛选依赖采集器保存的来源类型。
        self.assertTrue(all(row["source_type"] == "rss" for row in rows))

    @patch("collecter.fetch")
    def test_limit_prefers_newest_published_entries(self, fetch):
        """订阅源条目顺序混乱时，有限名额应优先留给最新发布时间。"""
        feed = b'''<rss version="2.0"><channel>
            <item><title>Old</title><link>https://example.com/old</link>
            <pubDate>Mon, 01 Jun 2026 00:00:00 GMT</pubDate></item>
            <item><title>New</title><link>https://example.com/new</link>
            <pubDate>Wed, 03 Jun 2026 00:00:00 GMT</pubDate></item>
            <item><title>Unknown</title><link>https://example.com/unknown</link></item>
            <item><title>Middle</title><link>https://example.com/middle</link>
            <pubDate>Tue, 02 Jun 2026 00:00:00 GMT</pubDate></item>
        </channel></rss>'''
        fetch.return_value = (feed, "https://example.com/feed", None)
        rows, errors = collecter.collect([
            {"name": "示例", "url": "https://example.com/feed", "max_articles": 2},
        ], [])
        self.assertEqual(errors, [])
        self.assertEqual([row["title"] for row in rows], ["New", "Middle"])


if __name__ == "__main__":
    # 支持直接运行这个测试文件。
    unittest.main()
