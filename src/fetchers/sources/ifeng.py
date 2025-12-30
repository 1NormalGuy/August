"""凤凰网抓取器"""

import json
import re
from typing import List

import httpx

from ..base import BaseFetcher
from ..models import Trend


class IfengFetcher(BaseFetcher):
    """凤凰网"""

    @property
    def source_id(self) -> str:
        return "ifeng"

    async def fetch(self) -> List[Trend]:
        url = "https://www.ifeng.com"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text

        match = re.search(r"var\s+allData\s*=\s*(\{[\s\S]*?\});", html)
        if not match:
            raise ValueError("无法从页面中提取数据")

        data = json.loads(match.group(1))
        raw_news = data.get("hotNews1", [])
        if not raw_news:
            return []

        items = []
        for news in raw_news:
            news_url = news.get("url", "")
            if not news_url:
                continue

            items.append(
                Trend(
                    id=news_url,
                    title=news.get("title", ""),
                    url=news_url,
                )
            )

        return items
