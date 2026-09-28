"""离线验证加权评分、模型结果校验和快照排序。"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import collecter
from app import rank
from app.llm import AIClient, AIError, AITruncatedError
from app.rank import rank_snapshot
from app.scoring import (calculate_score, company_source, priority_reference_sources,
                         reference_source, validate_assessment)

# 使用虚构配置验证评分逻辑不依赖特定接口或模型。
TEST_ENDPOINT = "https://example.com/v1/chat/completions"
TEST_MODEL = "example-model"


def assessment(dimensions, *, related=True):
    """生成完整的模拟模型输出，用于检验评分边界。"""
    return {
        "summary": "这是一条 AI 资讯。", "category": "研究", "tags": ["模型"],
        "is_ai_related": related, "dimensions": dimensions, "reason": "有具体的新发布信息。",
    }


class ScoringTests(unittest.TestCase):
    """检验权重、非 AI 降权、错误隔离及采集入口集成。"""

    def test_weighted_score_and_non_ai_gate(self):
        """总分应按固定权重计算；非 AI 新闻不能靠其他维度排到前面。"""
        values = {"relevance": 5, "impact": 4, "novelty": 3, "evidence": 2}
        self.assertEqual(calculate_score(True, values), 77)
        self.assertEqual(calculate_score(False, {key: 5 for key in values}), 0)
        item = validate_assessment(assessment(values))
        self.assertEqual(item["score"], 77)
        self.assertEqual(item["priority"], "中")
        self.assertEqual(item["weights"]["relevance"], 35)

    def test_invalid_model_scores(self):
        """缺失维度、布尔数值、越界数值及模型伪造的总分都应拒绝。"""
        dimensions = {"relevance": 5, "impact": 4, "novelty": 3, "evidence": 2}
        invalid = [
            assessment({**dimensions, "impact": True}),
            assessment({**dimensions, "impact": 6}),
            assessment({"relevance": 5}),
            {**assessment(dimensions), "score": 100},
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_assessment(value)

    def test_ai_analyze_one_call_and_bounded_body(self):
        """模型只收到限定长度的材料，并有足够输出配额完成评分。"""
        client = AIClient("fake", TEST_ENDPOINT, TEST_MODEL)
        dimensions = {"relevance": 5, "impact": 5, "novelty": 5, "evidence": 5}
        with patch.object(client, "chat", return_value={
            "content": json.dumps(assessment(dimensions)), "usage": {}, "model": "test",
        }) as chat:
            result = client.analyze({"title": "新模型", "source": "示例", "content": "甲" * 12001})
        self.assertEqual(result["article"]["score"], 100)
        self.assertEqual(len(json.loads(chat.call_args.args[0])["content"]), 12000)
        self.assertTrue(json.loads(chat.call_args.args[0])["content_truncated"])
        # 隐藏推理会消耗输出配额，验证评分请求不再使用过低的默认值。
        self.assertEqual(chat.call_args.kwargs["max_tokens"], 8192)
        with patch.object(client, "chat", return_value={
            "content": json.dumps({**assessment(dimensions), "dimensions": {"impact": 5}}),
            "usage": {}, "model": "test",
        }):
            with self.assertRaises(AIError):
                client.analyze({"title": "新模型"})

    def test_ai_analyze_retries_only_truncated_output(self):
        """评分输出截断时提高上限重试一次，其他错误保持单次调用。"""
        client = AIClient("fake", TEST_ENDPOINT, TEST_MODEL)
        valid = {"content": json.dumps(assessment({key: 4 for key in
                  ("relevance", "impact", "novelty", "evidence")})), "usage": {}, "model": "test"}
        with patch.object(client, "chat", side_effect=[AITruncatedError("截断"), valid]) as chat:
            self.assertEqual(client.analyze({"title": "新模型"})["article"]["score"], 80)
        self.assertEqual([call.kwargs["max_tokens"] for call in chat.call_args_list],
                         [8192, 16384])
        with patch.object(client, "chat", side_effect=AIError("无权限")) as chat:
            with self.assertRaises(AIError):
                client.analyze({"title": "新模型"})
        chat.assert_called_once()

    def test_rank_snapshot_keeps_failures_at_end(self):
        """高分在前，同分保持原顺序，失败文章保留且旧分数被清除。"""
        high = validate_assessment(assessment({key: 5 for key in
                                               ("relevance", "impact", "novelty", "evidence")}))
        low = validate_assessment(assessment({key: 1 for key in
                                              ("relevance", "impact", "novelty", "evidence")}))
        client = Mock()
        client.model = TEST_MODEL
        client.analyze.side_effect = [
            {"article": low}, AIError("模拟失败"), {"article": high}, {"article": high},
        ]
        payload = {"collected_at": "original", "errors": [], "articles": [
            {"title": "低", "score": 99}, {"title": "失败", "score": 99},
            {"title": "高一"}, {"title": "高二"},
        ]}
        ranked, failed = rank_snapshot(payload, client)
        self.assertEqual([row["title"] for row in ranked["articles"]],
                         ["高一", "高二", "低", "失败"])
        self.assertEqual(failed, 1)
        self.assertIsNone(ranked["articles"][-1]["score"])
        self.assertEqual(ranked["articles"][-1]["scoring_error"], "模拟失败")
        self.assertEqual(ranked["collected_at"], "original")
        self.assertEqual(ranked["ranking"]["scored"], 3)
        self.assertEqual(ranked["ranking"]["model"], TEST_MODEL)
        self.assertEqual(payload["articles"][0]["score"], 99)

    def test_official_domain_requires_real_hostname(self):
        """仅官网及其子域名自动认作公司来源，转载与伪装域名不加分。"""
        self.assertEqual(company_source({"url": "https://openai.com/news/a"}), "OpenAI")
        self.assertEqual(company_source({"url": "https://news.anthropic.com/a"}), "Anthropic")
        self.assertIsNone(company_source({
            "url": "https://openai.com.example.org/a", "title": "OpenAI 发布模型",
            "source": "OpenAI 资讯转载",
        }))
        self.assertIsNone(company_source({"url": "https://example.com/openai.com/a"}))
        self.assertEqual(company_source({
            "url": "https://example.com/converted-feed", "ai_company": "Mistral AI",
        }), "Mistral AI")

    def test_reference_groups_match_exact_feed_addresses(self):
        """三组及两个官网示例可加分；同域名其他账号和普通媒体不能冒充。"""
        sources = priority_reference_sources()
        self.assertEqual(len(sources), 42)
        catalog = json.loads((Path(collecter.__file__).parent / "docs/reference-sources.json")
                             .read_text(encoding="utf-8"))["sources"]
        for source_id in ("S023", "S042", "S051", "S059", "S127", "S128"):
            row = next(row for row in catalog if row["id"] == source_id)
            with self.subTest(source_id=source_id):
                matched = reference_source({"source_feed_url": row["url"]})
                self.assertEqual(matched["id"], source_id)
                self.assertEqual(matched["category"], row["category"])
        self.assertIsNone(reference_source({"source_feed_url": "https://api.xgo.ing/rss/user/unknown",
                                            "source": "OpenAI(@OpenAI)"}))
        self.assertIsNone(reference_source({"source_feed_url": catalog[0]["url"]}))

    def test_catalog_bonus_does_not_stack_with_official_domain(self):
        """参考组文章获得一次来源加分；同时命中官网仍只加一次。"""
        feed_url = next(url for url, row in priority_reference_sources().items()
                        if row["id"] == "S051")
        analysis = validate_assessment(assessment({key: 4 for key in
                                                   ("relevance", "impact", "novelty", "evidence")}))
        client = Mock()
        client.analyze.return_value = {"article": analysis}
        ranked, failed = rank_snapshot({"articles": [
            {"title": "Hugging Face 资讯", "source_feed_url": feed_url,
             "url": "https://example.com/article"},
            {"title": "OpenAI 官网资讯", "source_feed_url": feed_url,
             "url": "https://openai.com/article"},
        ]}, client)
        self.assertEqual(failed, 0)
        self.assertEqual([row["source_bonus"] for row in ranked["articles"]], [10, 10])
        self.assertTrue(all(row["rank_score"] == 90 for row in ranked["articles"]))
        self.assertEqual(ranked["articles"][0]["priority_source"]["id"], "S051")
        self.assertEqual(ranked["ranking"]["source_priority_bonus"], 10)

    @patch("collecter.time.sleep")
    @patch("collecter.fetch")
    def test_later_reference_feed_can_boost_duplicate_article(self, fetch, sleep):
        """聚合源先收录同一链接时，后续参考清单来源仍应得到加分。"""
        feed = (b'<rss version="2.0"><channel><item><title>Release</title>'
                b'<link>https://example.com/a</link></item></channel></rss>')
        fetch.return_value = (feed, "https://example.com/feed", None)
        selected = next(url for url, row in priority_reference_sources().items()
                        if row["id"] == "S023")
        rows, errors = collecter.collect([
            {"name": "聚合", "url": "https://example.com/feed"},
            {"name": "Qwen", "url": selected},
        ], [])
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_feed_urls"],
                         ["https://example.com/feed", selected])
        self.assertEqual(reference_source(rows[0])["id"], "S023")

    def test_company_bonus_changes_order_only_for_ai_news(self):
        """官方 AI 资讯在内容分基础上加 10 分；非 AI 官方文章不加分。"""
        official = validate_assessment(assessment({
            "relevance": 5, "impact": 4, "novelty": 3, "evidence": 2,
        }))
        general = validate_assessment(assessment({key: 4 for key in
                                                  ("relevance", "impact", "novelty", "evidence")}))
        unrelated = validate_assessment(assessment({key: 5 for key in
                                                    ("relevance", "impact", "novelty", "evidence")},
                                                   related=False))
        client = Mock()
        client.analyze.side_effect = [
            {"article": general}, {"article": official}, {"article": unrelated},
        ]
        ranked, failed = rank_snapshot({"articles": [
            {"title": "普通媒体", "url": "https://example.com/a"},
            {"title": "官方发布", "url": "https://openai.com/a"},
            {"title": "公司招聘", "url": "https://anthropic.com/jobs"},
        ]}, client)
        self.assertEqual(failed, 0)
        self.assertEqual([row["title"] for row in ranked["articles"]],
                         ["官方发布", "普通媒体", "公司招聘"])
        self.assertEqual(ranked["articles"][0]["score"], 77)
        self.assertEqual(ranked["articles"][0]["source_bonus"], 10)
        self.assertEqual(ranked["articles"][0]["rank_score"], 87)
        self.assertEqual(ranked["articles"][-1]["source_bonus"], 0)
        self.assertEqual(ranked["articles"][-1]["rank_score"], 0)

    @patch("collecter.fetch")
    def test_configured_company_survives_collection(self, fetch):
        """人工确认的公司 RSS 标记应进入文章快照供评分使用。"""
        feed = (b'<rss version="2.0"><channel><item><title>Release</title>'
                b'<link>https://example.com/a</link></item></channel></rss>')
        fetch.return_value = (feed, "https://example.com/feed", None)
        source = {"name": "官方订阅", "url": "https://example.com/feed", "ai_company": "Mistral AI"}
        rows, errors = collecter.collect([source], [])
        self.assertEqual(errors, [])
        self.assertEqual(rows[0]["ai_company"], "Mistral AI")
        self.assertEqual(rows[0]["source_feed_url"], source["url"])
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "sources.json"
            config.write_text(json.dumps({"rss": [source]}), encoding="utf-8")
            self.assertEqual(collecter.load_sources(config)[0][0]["ai_company"], "Mistral AI")
            config.write_text(json.dumps({"rss": [{**source, "ai_company": " "}]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                collecter.load_sources(config)

    @patch("collecter.time.sleep")
    @patch("collecter.fetch")
    def test_later_official_feed_marks_duplicate_article(self, fetch, sleep):
        """转载源先采到相同链接时，后续官方订阅仍能补全公司标记。"""
        feed = (b'<rss version="2.0"><channel><item><title>Release</title>'
                b'<link>https://example.com/a</link></item></channel></rss>')
        fetch.return_value = (feed, "https://example.com/feed", None)
        rows, errors = collecter.collect([
            {"name": "转载", "url": "https://example.com/feed"},
            {"name": "官方", "url": "https://example.com/official", "ai_company": "Mistral AI"},
        ], [])
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ai_company"], "Mistral AI")

    @patch("collecter.collect")
    @patch("app.llm.AIClient.from_env")
    def test_collector_defaults_to_config_and_scoring(self, from_env, collect):
        """无参数采集使用项目配置并默认保存模型排序结果。"""
        high = validate_assessment(assessment({key: 5 for key in
                                               ("relevance", "impact", "novelty", "evidence")}))
        low = validate_assessment(assessment({key: 1 for key in
                                              ("relevance", "impact", "novelty", "evidence")}))
        from_env.return_value.analyze.side_effect = [{"article": low}, {"article": high}]
        from_env.return_value.model = TEST_MODEL
        collect.return_value = ([{"title": "低"}, {"title": "高"}], [])
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config" / "sources.json"
            config.parent.mkdir()
            output = Path(directory) / "result.json"
            config.write_text(json.dumps({"rss": [{"name": "示例", "url": "https://example.com"}]}))
            # 模拟模型流程时隔离默认数据库，避免测试文章进入个人归档。
            with patch("collecter.ROOT", Path(directory)), patch("app.db.save_snapshot", return_value=(0, 0)), patch("app.db.cleanup_if_due", return_value=0), patch("sys.argv", ["collecter.py", "--output", str(output)]):
                self.assertEqual(collecter.main(), 0)
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(collect.call_args.args[0][0]["name"], "示例")
        from_env.assert_called_once()
        self.assertEqual([row["title"] for row in result["articles"]], ["高", "低"])
        self.assertEqual(result["ranking"]["scored"], 2)
        self.assertEqual(result["ranking"]["model"], TEST_MODEL)

    @patch("collecter.collect", return_value=([{"title": "只采集"}], []))
    @patch("app.llm.AIClient.from_env")
    def test_collector_no_score_skips_model(self, from_env, collect):
        """显式跳过评分时不读取 key，仍保存采集结果。"""
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "sources.json"
            output = Path(directory) / "result.json"
            config.write_text(json.dumps({"rss": [{"name": "示例", "url": "https://example.com"}]}))
            # 只验证命令开关，入库行为在数据库测试中单独覆盖。
            with patch("app.db.save_snapshot", return_value=(0, 0)), patch("app.db.cleanup_if_due", return_value=0), patch("sys.argv", ["collecter.py", "--sources", str(config),
                                    "--output", str(output), "--no-score"]):
                self.assertEqual(collecter.main(), 0)
            result = json.loads(output.read_text(encoding="utf-8"))
        from_env.assert_not_called()
        collect.assert_called_once()
        self.assertNotIn("ranking", result)

    @patch("app.rank.AIClient.from_env")
    def test_existing_snapshot_cli_preserves_metadata(self, from_env):
        """历史快照评分应保留采集时间和来源错误，并写入排序结果。"""
        high = validate_assessment(assessment({key: 5 for key in
                                               ("relevance", "impact", "novelty", "evidence")}))
        from_env.return_value.analyze.return_value = {"article": high}
        from_env.return_value.model = TEST_MODEL
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            output = Path(directory) / "ranked.json"
            source.write_text(json.dumps({
                "collected_at": "2026-09-01T00:00:00+00:00",
                "errors": [{"source": "其他", "error": "模拟失败"}],
                "articles": [{"title": "新发布"}],
            }), encoding="utf-8")
            # 历史快照评分测试只检查输出，不写真实本地数据库。
            with patch("app.db.save_snapshot"), patch("app.db.cleanup_if_due", return_value=0), patch("sys.argv", ["rank", "--input", str(source), "--output", str(output)]):
                self.assertEqual(rank.main(), 0)
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["collected_at"], "2026-09-01T00:00:00+00:00")
        self.assertEqual(result["errors"][0]["source"], "其他")
        self.assertEqual(result["articles"][0]["score"], 100)


if __name__ == "__main__":
    # 支持直接运行本文件，所有模型结果均为模拟数据。
    unittest.main()
