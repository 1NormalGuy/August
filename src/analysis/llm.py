"""AI 客户端模块 - 使用 LiteLLM 统一接口"""

import logging
import re
from typing import List, Optional

from litellm import acompletion

from src.core import cfg

logger = logging.getLogger(__name__)

# 内容截取长度限制
MAX_CONTENT_LENGTH = 12000

# 摘要生成 Prompt 模板
SUMMARY_PROMPT_TEMPLATE = """你是一个专业的新闻摘要助手。请根据以下内容生成简洁、准确的摘要。

**原始内容：**

{content}

**要求：**

1. 字数：250-300字
2. 结构清晰，分段呈现（2-3个自然段）
3. 保留关键信息、数据、人物、时间等要素
4. 使用客观、中立的语气
5. 避免主观评价和情绪化表达
6. 如果是争议话题，呈现多方观点
7. 保持逻辑连贯，易于理解

**输出格式：**

直接输出摘要内容，不需要标题或其他说明。"""


async def invoke_llm(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    调用 LLM 生成文本
    
    Args:
        prompt: 提示词
        temperature: 温度参数
        max_tokens: 最大 token 数
        
    Returns:
        生成的文本
    """
    if not cfg.llm_api_key:
        raise ValueError("LLM_API_KEY not set")

    response = await acompletion(
        model=cfg.llm_model,
        messages=[{"role": "user", "content": prompt}],
        api_key=cfg.llm_api_key,
        api_base=cfg.llm_api_base if cfg.llm_api_base else None,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content


async def generate_summaries(news_list: List[dict]) -> List[dict]:
    """
    为每条新闻生成摘要
    
    Args:
        news_list: 新闻列表，每个元素包含 title, url, markdown_content 等字段
        
    Returns:
        带摘要的新闻列表
    """
    if not cfg.llm_api_key:
        logger.error("LLM_API_KEY not set")
        return news_list

    results = []

    for i, news in enumerate(news_list, 1):
        logger.debug(f"处理 {i}/{len(news_list)}: {news['title'][:50]}...")

        prompt = _build_prompt(news)

        try:
            summary = await _generate_summary(prompt)
            news_copy = news.copy()
            news_copy["summary"] = summary
        except Exception as e:
            logger.error(f"LLM 调用失败（第 {i} 条）: {e}")
            news_copy = news.copy()
            news_copy["summary"] = ""

        results.append(news_copy)

    return results


def _build_prompt(news: dict) -> str:
    """构建摘要生成提示词"""
    if news.get("markdown_content"):
        content = news["markdown_content"][:MAX_CONTENT_LENGTH]
        if len(news["markdown_content"]) > MAX_CONTENT_LENGTH:
            content += "..."
    else:
        content = f"标题：{news['title']}\n\n（无法获取正文内容，请根据标题生成摘要）"

    return SUMMARY_PROMPT_TEMPLATE.format(content=content)


async def _generate_summary(prompt: str) -> str:
    """生成摘要"""
    try:
        content = await invoke_llm(prompt)
        logger.debug(f"AI 返回摘要成功，长度: {len(content)} 字符")

        summary = _extract_summary(content)

        if summary and len(summary) < 200:
            logger.warning(f"摘要太短（{len(summary)}字）: {summary[:100]}...")

        return summary

    except Exception as e:
        logger.error(f"AI API 调用失败: {e}")
        raise


def _extract_summary(response: str) -> str:
    """从 LLM 响应中提取摘要"""
    content = response.strip()
    if not content:
        return ""
    content = re.sub(r"^摘要[：:]\s*", "", content).strip()
    return content
