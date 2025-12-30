"""机器之心 RSS 抓取器"""

import logging
import re
from typing import List
from html import unescape

import httpx
import feedparser

from ..base import BaseFetcher
from ..models import Trend

logger = logging.getLogger(__name__)


class JiqizhixinFetcher(BaseFetcher):
    """机器之心 RSS 抓取器"""

    RSS_URL = "https://www.jiqizhixin.com/rss"

    @property
    def source_id(self) -> str:
        return "jiqizhixin"

    def _clean_html(self, html_text: str) -> str:
        """清理 HTML 标签，保留纯文本"""
        if not html_text:
            return ""
        clean = re.sub(r'<[^>]+>', '', html_text)
        clean = unescape(clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    async def fetch(self) -> List[Trend]:
        """抓取机器之心 RSS"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.RSS_URL, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })
                response.raise_for_status()

                feed = feedparser.parse(response.text)

                trends = []
                for i, entry in enumerate(feed.entries[:30], 1):
                    link = entry.get("link", "")
                    title = entry.get("title", "").strip()

                    if not title or not link:
                        continue

                    summary = entry.get("summary", "") or entry.get("description", "")
                    summary = self._clean_html(summary)
                    if len(summary) > 200:
                        summary = summary[:200] + "..."

                    trends.append(
                        Trend(
                            id=link,
                            title=title,
                            url=link,
                            score=1000 - i,
                            description=summary,
                        )
                    )

                logger.info(f"机器之心: 获取 {len(trends)} 条新闻")
                return trends

        except Exception as e:
            logger.error(f"机器之心抓取失败: {e}")
            return []
