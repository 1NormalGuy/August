"""今日头条抓取器"""

from typing import List

import httpx

from ..base import BaseFetcher
from ..models import Trend


class ToutiaoFetcher(BaseFetcher):
    """今日头条"""

    @property
    def source_id(self) -> str:
        return "toutiao"

    async def fetch(self) -> List[Trend]:
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        items = []
        for item in data.get("data", []):
            cluster_id = item.get("ClusterIdStr", "")
            if not cluster_id:
                continue

            hot_value = item.get("HotValue")
            items.append(
                Trend(
                    id=cluster_id,
                    title=item.get("Title", ""),
                    url=f"https://www.toutiao.com/trending/{cluster_id}/",
                    score=int(hot_value) if hot_value else None,
                )
            )

        return items
