"""华尔街见闻抓取器"""

from typing import List

import httpx

from ..base import BaseFetcher
from ..models import Trend


class WallstreetcnFetcher(BaseFetcher):
    """华尔街见闻"""

    @property
    def source_id(self) -> str:
        return "wallstreetcn"

    async def fetch(self) -> List[Trend]:
        url = "https://api-one.wallstcn.com/apiv1/content/information-flow?channel=global-channel&accept=article&limit=30"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        items_data = data.get("data", {}).get("items", [])
        if not items_data:
            return []

        items = []
        for item in items_data:
            resource_type = item.get("resource_type")
            if resource_type in ("theme", "ad"):
                continue

            resource = item.get("resource", {})
            if not resource:
                continue

            if resource.get("type") == "live":
                continue

            item_id = resource.get("id")
            if not item_id:
                continue

            uri = resource.get("uri", "")
            if not uri:
                continue

            title = resource.get("title") or resource.get("content_short", "")
            if not title:
                continue

            items.append(
                Trend(
                    id=str(item_id),
                    title=title,
                    url=uri,
                    description=resource.get("content_text"),
                )
            )

        return items
