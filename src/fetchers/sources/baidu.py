"""百度热搜抓取器"""

import json
import re
from typing import List
from urllib.parse import unquote

import httpx

from ..base import BaseFetcher
from ..models import Trend


class BaiduFetcher(BaseFetcher):
    """百度热搜"""

    @property
    def source_id(self) -> str:
        return "baidu"

    async def fetch(self) -> List[Trend]:
        url = "https://top.baidu.com/board?tab=realtime"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            raw_data = response.text

        match = re.search(r"<!--s-data:(.*?)-->", raw_data, re.DOTALL)
        if not match:
            raise ValueError("无法从页面中提取数据")

        data = json.loads(match.group(1))
        cards = data.get("data", {}).get("cards", [])
        if not cards:
            return []

        content = cards[0].get("content", [])
        items = []

        for item in content:
            if item.get("isTop"):
                continue

            raw_url = item.get("rawUrl", "")
            decoded_url = unquote(raw_url)

            items.append(
                Trend(
                    id=decoded_url,
                    title=item.get("word", ""),
                    url=decoded_url,
                    description=item.get("desc"),
                    score=int(item.get("hotScore")),
                )
            )

        return items
