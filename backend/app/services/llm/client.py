"""
LLM 服务客户端
支持 OpenAI 兼容的 API
"""
import os
import re
import time
from typing import AsyncGenerator, Optional
from openai import OpenAI
from loguru import logger
from app.core.config import settings


class LLMClient:
    """LLM 客户端"""

    def __init__(self):
        """初始化 LLM 客户端"""
        api_key = settings.openai_api_key or os.getenv("OPEN_AI_API_KEY")
        base_url = settings.openai_url or os.getenv("OPEN_AI_URL")
        model = settings.llm_model or os.getenv("LLM_MODEL", "qwen-plus")

        if not api_key:
            logger.warning("⚠️  OPEN_AI_API_KEY 未配置，LLM 功能不可用")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )
            logger.info(f"✅ LLM 客户端初始化成功: {base_url}")

        self.model = model
        self.system_prompt = self._get_default_system_prompt()

    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        return """你是一个友好的AI助手，擅长用自然、生动的方式与人交流。

你的回复应该：
1. 简洁明了，避免冗长
2. 口语化表达，像真人对话
3. 适当使用语气词，如"嗯"、"哦"、"呢"、"呀"
4. 回复长度控制在 50 字以内，除非用户需要详细解释

示例：
用户: "你好"
AI: "你好呀！我是AI助手，很高兴认识你！"

用户: "今天天气怎么样？"
AI: "抱歉哦，我暂时无法查询天气信息呢。你可以告诉我你在哪个城市，我可以帮你想想怎么查。"
"""

    async def chat_stream(self, message: str, system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        流式对话

        Args:
            message: 用户消息
            system_prompt: 可选的系统提示词

        Yields:
            str: LLM 生成的文本片段
        """
        if not self.client:
            logger.error("❌ LLM 客户端未初始化")
            return

        start = time.perf_counter()

        try:
            messages = [
                {"role": "system", "content": system_prompt or self.system_prompt},
                {"role": "user", "content": message}
            ]

            logger.info(f"[LLM] 发送消息: {message[:50]}...")

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                stream_options={"include_usage": True}
            )

            first = True
            for chunk in completion:
                if len(chunk.choices) > 0:
                    if first:
                        first = False
                        ttf = time.perf_counter() - start
                        logger.info(f"[LLM] 首字延迟: {ttf:.3f}s")

                    msg = chunk.choices[0].delta.content

                    # 检查 msg 是否为 None
                    if msg is None:
                        continue

                    # 实时输出每个字符
                    logger.debug(f"[LLM] 生成: {msg}")
                    yield msg

            total = time.perf_counter() - start
            logger.info(f"[LLM] 总耗时: {total:.3f}s")

        except Exception as e:
            logger.error(f"[LLM] 生成失败: {e}")
            yield f"抱歉，我遇到了一些问题：{str(e)}"

    async def chat(self, message: str, system_prompt: Optional[str] = None) -> str:
        """
        非流式对话

        Args:
            message: 用户消息
            system_prompt: 可选的系统提示词

        Returns:
            str: LLM 完整回复
        """
        if not self.client:
            logger.error("❌ LLM 客户端未初始化")
            return "抱歉，LLM 服务未配置。"

        try:
            messages = [
                {"role": "system", "content": system_prompt or self.system_prompt},
                {"role": "user", "content": message}
            ]

            logger.info(f"[LLM] 发送消息: {message[:50]}...")

            start = time.perf_counter()
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            total = time.perf_counter() - start

            result = completion.choices[0].message.content
            logger.info(f"[LLM] 回复: {result[:50]}... (耗时: {total:.3f}s)")

            return result

        except Exception as e:
            logger.error(f"[LLM] 生成失败: {e}")
            return f"抱歉，我遇到了一些问题：{str(e)}"

    def set_system_prompt(self, prompt: str):
        """设置系统提示词"""
        self.system_prompt = prompt
        logger.info(f"[LLM] 系统提示词已更新")

    def is_available(self) -> bool:
        """检查 LLM 是否可用"""
        return self.client is not None


# 全局单例
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端单例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
