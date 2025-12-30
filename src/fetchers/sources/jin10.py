"""金十数据抓取器"""

import json
import re
import time
from typing import List

import httpx

from ..base import BaseFetcher
from ..models import Trend


class Jin10Fetcher(BaseFetcher):
    """金十数据"""

    @property
    def source_id(self) -> str:
        return "jin10"

    async def fetch(self) -> List[Trend]:
        timestamp = int(time.time() * 1000)
        url = f"https://www.jin10.com/flash_newest.js?t={timestamp}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            raw_data = response.text

        json_str = (
            raw_data.replace("var newest = ", "")
            .replace("var newest=", "")
            .rstrip(";")
            .strip()
        )
        data = json.loads(json_str)

        items = []
        for item in data:
            if item.get("channel") and 5 in item.get("channel", []):
                continue

            item_data = item.get("data", {})
            title = item_data.get("title") or item_data.get("content")
            if not title:
                continue

            text = re.sub(r"</?b>", "", title)
            match = re.match(r"^【([^】]*)】(.*)$", text)
            if match:
                item_title = match.group(1)
                item_desc = match.group(2).strip()
            else:
                item_title = text
                item_desc = None

            item_id = item.get("id")
            if not item_id:
                continue

            items.append(
                Trend(
                    id=str(item_id),
                    title=item_title,
                    url=f"https://flash.jin10.com/detail/{item_id}",
                    description=item_desc,
                )
            )

        return items
