"""校验模型评分并按固定权重计算 AI 资讯的重要性。"""

from functools import lru_cache
import json
from pathlib import Path
from urllib.parse import urlsplit

# 权重合计为 100；修改排序策略时只需调整这里及对应评分说明。
WEIGHTS = {"relevance": 35, "impact": 30, "novelty": 20, "evidence": 15}
SCORE_KEYS = frozenset(WEIGHTS)
# 优先来源在内容分之外加分，保留原有内容评分便于解释排序。
SOURCE_PRIORITY_BONUS = 10
# 只用明确的官网域名自动识别；其他官方账号可在来源配置中声明 ai_company。
OFFICIAL_DOMAINS = {"openai.com": "OpenAI", "anthropic.com": "Anthropic"}
# 候选目录只用于来源识别，不会因进入优先组而自动启用采集。
PRIORITY_CATEGORIES = frozenset({"中国AI公司", "AI Companies", "Dev Tools"})
# 两个官网示例订阅源虽在“OPML 示例”组，仍按 OpenAI 与 Hugging Face 来源处理。
PRIORITY_REFERENCE_IDS = frozenset({"S127", "S128"})
REFERENCE_CATALOG = Path(__file__).resolve().parents[1] / "docs" / "reference-sources.json"


@lru_cache(maxsize=1)
def priority_reference_sources() -> dict[str, dict[str, str]]:
    """加载三个优先分组和两个官网示例的订阅地址，仅保留排序字段。"""
    catalog = json.loads(REFERENCE_CATALOG.read_text(encoding="utf-8"))
    sources = {}
    for row in catalog["sources"]:
        if row.get("category") not in PRIORITY_CATEGORIES and row.get("id") not in PRIORITY_REFERENCE_IDS:
            continue
        item = {"id": row["id"], "name": row["name"], "category": row["category"]}
        # RSS 转换服务常共用域名，必须匹配完整订阅地址而非主机名。
        for key in ("url", "effective_url"):
            if isinstance(row.get(key), str):
                sources[row[key]] = item
    return sources


def reference_source(article: dict) -> dict[str, str] | None:
    """用所有采集订阅地址识别参考清单来源，不依赖可伪装的来源名称。"""
    feed_urls = article.get("source_feed_urls")
    if not isinstance(feed_urls, list):
        feed_urls = [article.get("source_feed_url"), article.get("feed_url")]
    sources = priority_reference_sources()
    for feed_url in feed_urls:
        if isinstance(feed_url, str) and feed_url in sources:
            return sources[feed_url]
    return None


def company_source(article: dict) -> str | None:
    """从人工标记或文章官网域名识别 AI 公司；正文提及公司不算官方来源。"""
    configured = article.get("ai_company")
    if isinstance(configured, str) and configured.strip():
        return configured.strip()
    url = article.get("url")
    if not isinstance(url, str):
        return None
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower().rstrip(".")
    except ValueError:
        return None
    if parts.scheme.lower() not in {"http", "https"}:
        return None
    # 点号边界防止 openai.com.example.org 一类伪装域名误获加分。
    for domain, company in OFFICIAL_DOMAINS.items():
        if host == domain or host.endswith("." + domain):
            return company
    return None


def calculate_score(is_ai_related: bool, dimensions: dict) -> int:
    """根据四项 0–5 整数评分返回 0–100 分；非 AI 资讯固定为 0 分。"""
    if type(is_ai_related) is not bool or not isinstance(dimensions, dict):
        raise ValueError("评分类型不正确")
    if set(dimensions) != SCORE_KEYS or any(
        type(value) is not int or not 0 <= value <= 5 for value in dimensions.values()
    ):
        raise ValueError("评分维度必须是完整的 0–5 整数")
    if not is_ai_related:
        return 0
    # 整数运算采用四舍五入，避免浮点误差影响临界排序。
    return (sum(WEIGHTS[key] * dimensions[key] for key in WEIGHTS) + 2) // 5


def validate_assessment(value: object) -> dict:
    """检查模型输出结构并加入可复算的总分；不信任模型直接给出的总分。"""
    required = {"summary", "category", "tags", "is_ai_related", "dimensions", "reason"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("评分字段不完整")
    if any(not isinstance(value[key], str) or not value[key].strip()
           for key in ("summary", "category", "reason")):
        raise ValueError("摘要、分类或评分理由为空")
    if not isinstance(value["tags"], list) or any(
        not isinstance(tag, str) or not tag.strip() for tag in value["tags"]
    ):
        raise ValueError("标签格式不正确")
    score = calculate_score(value["is_ai_related"], value["dimensions"])
    # 保留逐项分数和权重，方便以后调整策略及解释排序。
    return {**value, "score": score, "priority": (
        "高" if score >= 80 else "中" if score >= 60 else "低"
    ), "weights": WEIGHTS.copy()}
