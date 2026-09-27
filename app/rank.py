"""对采集快照逐篇调用 Qwen 评分，并将重要资讯排在前面。"""

import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

from app.qwen import MODEL, QwenClient, QwenError
from app.scoring import SOURCE_PRIORITY_BONUS, WEIGHTS, company_source, reference_source


def rank_snapshot(payload: dict, client: QwenClient) -> tuple[dict, int]:
    """对快照中的每篇资讯评分；单篇失败保留原文并放到列表末尾。"""
    if not isinstance(payload, dict) or not isinstance(payload.get("articles"), list):
        raise ValueError("快照必须包含 articles 列表")
    if any(not isinstance(article, dict) for article in payload["articles"]):
        raise ValueError("articles 中的每项都必须是对象")
    articles = []
    failed = 0
    for article in payload["articles"]:
        # 重评时移除旧结果，防止失败文章残留过期分数。
        item = {key: value for key, value in article.items()
                if key not in {"ai_analysis", "score", "rank_score", "source_bonus",
                               "official_ai_company", "priority_source", "priority", "scoring_error"}}
        try:
            result = client.analyze(item)
            analysis = result["article"]
            company = company_source(item)
            reference = reference_source(item)
            # 同时命中官网和参考目录只加一次；目录分组不等于官方身份认证。
            priority_source = (
                {"kind": "reference", **reference} if reference else
                {"kind": "company", "name": company} if company else None
            )
            bonus = SOURCE_PRIORITY_BONUS if priority_source and analysis["is_ai_related"] else 0
            item["ai_analysis"] = analysis
            item["score"] = analysis["score"]
            item["source_bonus"] = bonus
            item["rank_score"] = analysis["score"] + bonus
            item["official_ai_company"] = company
            item["priority_source"] = priority_source
            item["priority"] = (
                "高" if item["rank_score"] >= 80 else "中" if item["rank_score"] >= 60 else "低"
            )
        except (QwenError, ValueError) as exc:
            failed += 1
            item["score"] = None
            item["rank_score"] = None
            item["source_bonus"] = 0
            item["official_ai_company"] = company_source(item)
            item["priority_source"] = None
            item["priority"] = "未评分"
            item["scoring_error"] = str(exc)
        articles.append(item)
    # 按加分后的排序分数排列；同分保留采集顺序，未评分文章放在最后。
    articles.sort(key=lambda item: (item["rank_score"] is not None, item["rank_score"] or 0),
                  reverse=True)
    ranked = {**payload, "articles": articles, "ranking": {
        "model": MODEL, "weights": WEIGHTS.copy(), "source_priority_bonus": SOURCE_PRIORITY_BONUS,
        "scored": len(articles) - failed, "failed": failed,
    }}
    return ranked, failed


def write_snapshot(path: Path, payload: dict) -> None:
    """原子写入排序结果，避免调用中断破坏现有快照。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main() -> int:
    """读取已有采集快照，评分后另存 JSON，并在终端显示前十条。"""
    parser = argparse.ArgumentParser(description="使用 Qwen 为 AI 资讯加权评分并排序")
    parser.add_argument("--input", type=Path, required=True, help="采集器输出的 JSON 快照")
    parser.add_argument("--output", type=Path, required=True, help="排序后的 JSON 路径")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        ranked, failed = rank_snapshot(payload, QwenClient.from_env())
        write_snapshot(args.output, ranked)
        # 评分后的同一快照同步入库，页面刷新即可看到新的排序分。
        from app.db import cleanup_if_due, save_snapshot
        from app.snapshots import cleanup_expired_snapshots
        save_snapshot(ranked)
        cleanup_if_due()
        # 评分结果入库成功后检查过期快照，避免旧 JSON 持续占用磁盘。
        cleanup_expired_snapshots()
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, sqlite3.Error, QwenError) as exc:
        print(f"评分失败：{exc}", file=sys.stderr)
        return 1
    for article in ranked["articles"][:10]:
        score = article["rank_score"] if article["rank_score"] is not None else "未评分"
        # 显示来源加分，避免读者把排序分数误认为纯内容分。
        bonus = f'（优先来源 +{article["source_bonus"]}）' if article["source_bonus"] else ""
        print(f'{score:>3}  {article.get("title", "无标题")}{bonus}')
    print(f"已保存 {len(ranked['articles'])} 条资讯；{failed} 条评分失败：{args.output}")
    return 1 if failed else 0


if __name__ == "__main__":
    # 导入模块时不触发模型调用，便于采集器复用。
    raise SystemExit(main())
