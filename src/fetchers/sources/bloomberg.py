"""彭博社 RSS 抓取器（含AI翻译）"""

import asyncio
import re
import logging
from typing import List

import httpx
import feedparser
from litellm import acompletion

from src.core import cfg
from ..base import BaseFetcher
from ..models import Trend

logger = logging.getLogger(__name__)

# 类别中英映射
CATEGORY_CN = {
    "markets": "市场",
    "technology": "科技",
    "politics": "政治",
    "business": "商业",
    "economics": "经济",
}


class BloombergFetcher(BaseFetcher):
    """彭博社 RSS 聚合抓取器（多频道，带中文翻译）"""

    RSS_FEEDS = {
        "markets": "https://feeds.bloomberg.com/markets/news.rss",
        "technology": "https://feeds.bloomberg.com/technology/news.rss",
        "politics": "https://feeds.bloomberg.com/politics/news.rss",
        "business": "https://feeds.bloomberg.com/business/news.rss",
        "economics": "https://feeds.bloomberg.com/economics/news.rss",
    }

    @property
    def source_id(self) -> str:
        return "bloomberg"

    async def _translate_titles(self, titles: List[str]) -> List[str]:
        """批量翻译标题为中文"""
        if not titles or not cfg.llm_api_key:
            logger.warning("翻译跳过: 无标题或无API密钥")
            return titles

        titles_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(titles)])
        prompt = f"""请将以下英文新闻标题翻译成简洁的中文，保持新闻标题风格。
要求：
1. 每行输出一个翻译结果
2. 不要输出序号
3. 保持原标题的含义和风格
4. 共{len(titles)}条，必须输出{len(titles)}行

原文：
{titles_text}"""

        try:
            response = await acompletion(
                model=cfg.llm_model,
                messages=[{"role": "user", "content": prompt}],
                api_key=cfg.llm_api_key,
                api_base=cfg.llm_api_base,
                timeout=60,
            )

            translated = response.choices[0].message.content.strip()
            lines = []
            for line in translated.split("\n"):
                line = line.strip()
                if not line:
                    continue
                line = re.sub(r'^[\d]+[\.\、\)\]\s]+', '', line).strip()
                if line:
                    lines.append(line)

            logger.info(f"翻译结果: 输入{len(titles)}条, 输出{len(lines)}条")

            if len(lines) == len(titles):
                logger.info(f"翻译成功: {lines[:3]}...")
                return lines
            else:
                logger.warning(f"翻译结果数量不匹配: {len(lines)} vs {len(titles)}")
                return titles

        except Exception as e:
            logger.error(f"翻译失败: {e}")
            return titles

    async def fetch(self) -> List[Trend]:
        """抓取彭博社多个频道的 RSS 并翻译为中文"""
        all_items = []
        seen_links = set()

        async with httpx.AsyncClient(timeout=30.0) as client:
            for category, url in self.RSS_FEEDS.items():
                try:
                    response = await client.get(url, headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                    })
                    response.raise_for_status()

                    feed = feedparser.parse(response.text)

                    for entry in feed.entries[:10]:
                        link = entry.get("link", "")
                        if link in seen_links:
                            continue
                        seen_links.add(link)

                        title = entry.get("title", "").strip()
                        if not title:
                            continue

                        summary = entry.get("summary", "")
                        if len(summary) > 200:
                            summary = summary[:200] + "..."

                        all_items.append({
                            "title": title,
                            "link": link,
                            "summary": summary,
                            "category": category,
                        })

                except Exception as e:
                    logger.warning(f"Bloomberg {category} 抓取失败: {e}")
                    continue

        all_items = all_items[:40]

        if not all_items:
            return []

        # 批量翻译标题
        original_titles = [item["title"] for item in all_items]
        translated_titles = []

        batch_size = 10
        for i in range(0, len(original_titles), batch_size):
            batch = original_titles[i:i+batch_size]
            translated_batch = await self._translate_titles(batch)
            translated_titles.extend(translated_batch)
            if i + batch_size < len(original_titles):
                await asyncio.sleep(0.5)

        # 转换为 Trend 对象
        trends = []
        for i, item in enumerate(all_items):
            category_cn = CATEGORY_CN.get(item["category"], item["category"])
            title_cn = translated_titles[i] if i < len(translated_titles) else item["title"]

            trends.append(
                Trend(
                    id=item["link"],
                    title=f"[{category_cn}] {title_cn}",
                    url=item["link"],
                    score=1000 - i,
                    description=item.get("summary", ""),
                )
            )

        logger.info(f"彭博社: 获取并翻译 {len(trends)} 条新闻")
        return trends
