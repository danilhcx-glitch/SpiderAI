"""兼容旧模块入口；新代码请从 app.llm 导入通用模型客户端。"""

from app.llm import AIClient, AIError, AITruncatedError, main

# 保留旧导入名称和命令行入口，配置仍统一读取 AI_API_* 与 AI_MODEL。
QwenClient = AIClient
QwenError = AIError
QwenTruncatedError = AITruncatedError


if __name__ == "__main__":
    # 历史命令委托给通用入口，避免维护两套请求实现。
    raise SystemExit(main())
