"""验证本地页面读取 SQLite 或指定快照，且不会暴露其他文件。"""

from datetime import datetime, timezone
import json
from io import BytesIO
from pathlib import Path
import tempfile
import unittest

from app.web import load_snapshot, make_handler, source_groups, to_frontend_data
from app.db import save_snapshot


class WebTests(unittest.TestCase):
    """覆盖快照选择、SQLite 查询和本地只读 HTTP 路由。"""

    def test_latest_valid_snapshot(self):
        """最新的非资讯 JSON 不应遮住较早生成的有效采集结果。"""
        with tempfile.TemporaryDirectory() as directory:
            data_root = Path(directory)
            (data_root / "articles.json").write_text(
                json.dumps({"articles": [{"title": "测试", "url": "https://example.com"}]}),
                encoding="utf-8",
            )
            (data_root / "other.json").write_text('{"sources": []}', encoding="utf-8")
            self.assertEqual(load_snapshot(data_root=data_root)["articles"][0]["title"], "测试")

    def test_http_routes(self):
        """无须打开网络端口，也能验证固定页面、接口和拒绝路径。"""
        with tempfile.TemporaryDirectory() as directory:
            data_root = Path(directory)
            dist_root = data_root / "dist"
            (dist_root / "assets").mkdir(parents=True)
            (dist_root / "index.html").write_text("<title>SpiderAI</title>", encoding="utf-8")
            (dist_root / "assets" / "app.js").write_text("// 构建产物", encoding="utf-8")
            (data_root / "articles.json").write_text(
                json.dumps({"collected_at": "2026-09-27T00:00:00Z", "articles": []}),
                encoding="utf-8",
            )
            # 默认接口应读取临时 SQLite，而不是目录中的旧 JSON 文件。
            save_snapshot({"collected_at": datetime.now(timezone.utc).isoformat(), "articles": [
                {"title": "已入库", "url": "https://example.com/news", "source": "测试来源"},
            ]}, data_root / "spiderai.sqlite3")
            handler_class = make_handler(data_root=data_root, dist_root=dist_root)

            def request(path):
                """模拟处理器输出，避免测试环境的套接字权限影响结果。"""
                handler = handler_class.__new__(handler_class)
                handler.path = path
                handler.wfile = BytesIO()
                status = []
                handler.send_response = lambda code: status.append(code)
                handler.send_header = lambda *_: None
                handler.end_headers = lambda: None
                handler.send_error = lambda code, *_: status.append(code)
                handler.do_GET()
                return status[0], handler.wfile.getvalue()

            self.assertIn("SpiderAI", request("/")[1].decode("utf-8"))
            self.assertEqual(json.loads(request("/api/news")[1])["items"][0]["title"], "已入库")
            self.assertIn("构建产物", request("/assets/app.js")[1].decode("utf-8"))
            self.assertEqual(request("/api/news?range=bad")[0], 400)
            self.assertEqual(request("/config/sources.json")[0], 404)

    def test_snapshot_adapter(self):
        """原版页面应收到正确的时间窗口、来源分类和稳定文章 ID。"""
        now = datetime(2026, 9, 27, 12, tzinfo=timezone.utc)
        snapshot = {"collected_at": "2026-09-27T11:00:00Z", "articles": [
            {"title": "近期 RSS", "url": "https://example.com/a", "source": "示例 RSS",
             "source_type": "rss", "published_at": "2026-09-27T10:00:00Z", "rank_score": 91},
            {"title": "前天公众号", "url": "https://example.com/b", "source": "示例号",
             "source_type": "wechat", "published_at": "2026-09-25T10:00:00Z"},
            {"title": "脚本链接", "url": "javascript:alert(1)", "source_type": "url"},
        ]}
        daily = to_frontend_data(snapshot, "24h", now)
        weekly = to_frontend_data(snapshot, "7d", now)
        self.assertEqual([item["title"] for item in daily["items"]], ["近期 RSS"])
        self.assertEqual([item["site_id"] for item in weekly["items"]], ["rss", "wechat"])
        self.assertEqual(daily["items"][0]["rank_score"], 91)
        self.assertEqual(daily["items"][0]["id"], weekly["items"][0]["id"])
        self.assertEqual(source_groups(snapshot, "24h", now)[0]["feeds"][0]["name"], "示例 RSS")

    def test_favorite_http_routes(self):
        """收藏迁移、新增、读取、取消和错误输入均走本地 JSON 接口。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            handler_class = make_handler(data_root=root, dist_root=root)

            def request(method, path, payload=None, content_type="application/json"):
                """模拟本地 HTTP 请求并收集状态码与 JSON 响应。"""
                handler = handler_class.__new__(handler_class)
                handler.path = path
                handler.wfile = BytesIO()
                body = json.dumps(payload).encode("utf-8") if payload is not None else b""
                handler.rfile = BytesIO(body)
                handler.headers = {"Content-Type": content_type, "Content-Length": str(len(body))}
                status = []
                handler.send_response = lambda code: status.append(code)
                handler.send_header = lambda *_: None
                handler.end_headers = lambda: None
                handler.send_error = lambda code, *_: status.append(code)
                getattr(handler, method)()
                return status[0], handler.wfile.getvalue()

            legacy = {"https://example.com/old": {"title": "旧收藏", "timestamp": 1234567890000}}
            status, body = request("do_POST", "/api/favorites/import", {"favorites": legacy})
            self.assertEqual(status, 200)
            self.assertIn("https://example.com/old", json.loads(body)["favorites"])
            self.assertEqual(request("do_POST", "/api/favorites", {
                "url": "https://example.com/new", "title": "新收藏",
            })[0], 200)
            self.assertEqual(len(json.loads(request("do_GET", "/api/favorites")[1])["favorites"]), 2)
            self.assertEqual(request("do_POST", "/api/favorites", {
                "url": "https://example.com/bad", "title": "无效",
            }, "text/plain")[0], 400)
            self.assertEqual(request("do_DELETE", "/api/favorites")[0], 400)
            self.assertEqual(request("do_DELETE", "/api/favorites?url=https%3A%2F%2Fexample.com%2Fold")[0], 200)
            self.assertEqual(request("do_DELETE", "/api/favorites/all")[0], 200)
            self.assertEqual(json.loads(request("do_GET", "/api/favorites")[1])["favorites"], {})


if __name__ == "__main__":
    unittest.main()
