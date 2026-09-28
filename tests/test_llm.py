"""离线验证通用模型请求与响应处理；使用模拟请求，不调用真实平台。"""

import json
import os
import unittest
from unittest.mock import Mock, patch

import requests

from app.llm import AIClient, AIError

# 测试地址和模型均为虚构值，确保断言不依赖某一家服务商。
ENDPOINT = "https://example.com/v1/chat/completions"
MODEL = "example-model"


def reply(content="你好", reason="stop"):
    """构造最小成功响应，可替换正文和结束原因来覆盖异常场景。"""
    return Mock(status_code=200, json=Mock(return_value={
        "choices": [{"message": {"content": content}, "finish_reason": reason}],
        "usage": {"total_tokens": 10},
    }))


class AITests(unittest.TestCase):
    """覆盖请求约定、配置加载、异常提示和结构化摘要校验。"""

    @patch("app.llm.requests.post")
    def test_request_contract(self, post):
        """检查认证前缀、模型、消息、超时和重定向设置符合约定。"""
        post.return_value = reply()
        result = AIClient("Bearer fake-test-key", ENDPOINT, MODEL).chat("测试")
        self.assertEqual(result["content"], "你好")
        self.assertEqual(result["usage"]["total_tokens"], 10)
        args, kwargs = post.call_args
        self.assertEqual(args, (ENDPOINT,))
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer fake-test-key")
        self.assertEqual(kwargs["json"]["model"], MODEL)
        self.assertEqual(kwargs["json"]["messages"][1]["content"], "测试")
        self.assertFalse(kwargs["allow_redirects"])
        self.assertEqual(kwargs["timeout"], (10, 120))

    @patch("app.llm.requests.post")
    def test_missing_key_or_empty_input_never_sends(self, post):
        """无效输入应在本地失败，不能发出网络请求。"""
        with self.assertRaises(AIError):
            AIClient("", ENDPOINT, MODEL)
        with self.assertRaises(AIError):
            AIClient("fake", ENDPOINT, MODEL).chat(" ")
        post.assert_not_called()

    @patch("app.llm.load_dotenv")
    @patch.dict(os.environ, {"AI_API_KEY": "fake-env-key", "AI_API_URL": ENDPOINT,
                                 "AI_MODEL": MODEL}, clear=True)
    @patch("app.llm.requests.post", return_value=reply())
    def test_environment_key(self, post, dotenv):
        """使用环境变量中的密钥，且加载 .env 时不允许覆盖已有配置。"""
        AIClient.from_env().chat("你好")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer fake-env-key")
        self.assertEqual(post.call_args.args, (ENDPOINT,))
        self.assertEqual(post.call_args.kwargs["json"]["model"], MODEL)
        self.assertFalse(dotenv.call_args.kwargs["override"])

    @patch("app.llm.load_dotenv")
    @patch.dict(os.environ, {"AI_API_KEY": "", "AI_API_URL": ENDPOINT,
                                 "AI_MODEL": MODEL}, clear=True)
    def test_missing_environment_key(self, dotenv):
        """密钥为空时应提示新配置名，不向旧服务商配置回退。"""
        with self.assertRaisesRegex(AIError, "AI_API_KEY"):
            AIClient.from_env()
        dotenv.assert_called_once()

    def test_invalid_endpoint_and_model(self):
        """阻止向明文远程地址发送密钥，并在请求前识别错误配置。"""
        for endpoint in ("", "https://", "http://example.com/v1/chat/completions",
                         "https://user:pass@example.com/v1/chat/completions",
                         "https://example.com/v1/chat/completions#fragment"):
            with self.subTest(endpoint=endpoint), self.assertRaises(AIError):
                AIClient("fake", endpoint, MODEL)
        with self.assertRaisesRegex(AIError, "AI_MODEL"):
            AIClient("fake", ENDPOINT, " ")
        with self.assertRaisesRegex(AIError, "AI_TOKEN_PARAM"):
            AIClient("fake", ENDPOINT, MODEL, "unexpected")
        # 本机模型服务允许 HTTP，便于在本地运行兼容接口。
        self.assertEqual(AIClient("fake", "http://localhost:8000/v1/chat/completions",
                                  MODEL).model, MODEL)

    @patch("app.llm.requests.post", return_value=reply())
    def test_alternate_token_parameter(self, post):
        """可为要求新输出长度字段的兼容服务切换请求参数。"""
        AIClient("fake", ENDPOINT, MODEL, "max_completion_tokens").chat("你好")
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["max_completion_tokens"], 2048)
        self.assertNotIn("max_tokens", body)
        self.assertNotIn("temperature", body)

    @patch("app.llm.requests.post")
    def test_http_errors_do_not_echo_secret_or_retry(self, post):
        """HTTP 错误包含状态码，但不回显密钥，也不自动重试。"""
        for status in (302, 400, 401, 403, 404, 429, 500):
            with self.subTest(status=status):
                post.reset_mock()
                post.return_value = Mock(status_code=status, text="secret-key")
                with self.assertRaises(AIError) as exc:
                    AIClient("secret-key", ENDPOINT, MODEL).chat("你好")
                self.assertNotIn("secret-key", str(exc.exception))
                self.assertIn(str(status), str(exc.exception))
                post.assert_called_once()

    @patch("app.llm.requests.post")
    def test_network_failures(self, post):
        """超时或连接失败时隐藏底层异常中的敏感细节。"""
        for error in (requests.Timeout, requests.ConnectionError):
            post.side_effect = error("sensitive details")
            with self.assertRaises(AIError) as exc:
                AIClient("fake", ENDPOINT, MODEL).chat("你好")
            self.assertNotIn("sensitive details", str(exc.exception))

    @patch("app.llm.requests.post")
    def test_bad_response_and_truncation(self, post):
        """空答案、截断答案和格式错误的响应均应被拒绝。"""
        for response in (reply("", "stop"), reply("partial", "length"),
                         Mock(status_code=200, json=Mock(return_value={})),
                         Mock(status_code=200, json=Mock(side_effect=ValueError))):
            post.return_value = response
            with self.assertRaises(AIError):
                AIClient("fake", ENDPOINT, MODEL).chat("你好")

    @patch("app.llm.requests.post")
    def test_summary_validation(self, post):
        """接受合法摘要，拒绝非 JSON、缺失字段或类型错误的结果。"""
        item = {"summary": "模型发布", "category": "研究", "tags": ["开源"], "is_ai_related": True}
        post.return_value = reply(json.dumps(item))
        self.assertEqual(AIClient("fake", ENDPOINT, MODEL).summarize("原文")["article"], item)
        for content in ("不是 JSON", "[]", "{}", json.dumps({**item, "is_ai_related": "true"})):
            post.return_value = reply(content)
            with self.assertRaises(AIError):
                AIClient("fake", ENDPOINT, MODEL).summarize("原文")


if __name__ == "__main__":
    unittest.main()
