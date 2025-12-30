"""财联社抓取器"""

import hashlib
from typing import List
from urllib.parse import urlencode

import httpx

from ..base import BaseFetcher
from ..models import Trend


class CailianFetcher(BaseFetcher):
    """财联社"""

    @property
    def source_id(self) -> str:
        return "cailian"

    def _generate_sign(self, params: dict) -> str:
        """生成请求签名"""
        sorted_params = sorted(params.items())
        query_string = urlencode(sorted_params)
        sha1_hash = hashlib.sha1(query_string.encode()).hexdigest()
        sign = hashlib.md5(sha1_hash.encode()).hexdigest()
        return sign

    async def fetch(self) -> List[Trend]:
        url = "https://www.cls.cn/v2/article/hot/list"

        params = {
            "appName": "CailianpressWeb",
            "os": "web",
            "sv": "7.7.5",
        }

        sign = self._generate_sign(params)
        params["sign"] = sign

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://www.cls.cn/",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        items_data = data.get("data", [])
        if not items_data:
            return []

        items = []
        for item in items_data:
            item_id = item.get("id")
            if not item_id:
                continue

            brief = item.get("brief", "")
            title = item.get("title") or (brief.split("\n", 1)[0].strip() if brief else "")
            if not title:
                continue

            items.append(
                Trend(
                    id=str(item_id),
                    title=title,
                    url=f"https://www.cls.cn/detail/{item_id}",
                    description=item.get("brief"),
                )
            )

        return items
