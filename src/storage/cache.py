"""缓存存储"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from src.fetchers.models import Trend


@dataclass
class CacheData:
    """缓存文件数据结构"""

    source: str
    """源ID"""

    timestamp: str
    """时间戳，格式：2025-11-22 17:50:00"""

    items: List[Trend]
    """热门内容列表"""


def omit_empty(data: Any) -> Any:
    """递归移除字典中的 None 值"""
    if isinstance(data, dict):
        return {k: omit_empty(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [omit_empty(item) for item in data]
    else:
        return data


class CacheStorage:
    """缓存存储（保存到 temp 目录）"""

    def __init__(self, base_path: Optional[Path] = None):
        from src.core import cfg
        self.base_path = base_path or cfg.temp_dir

    def save(self, source_id: str, items: List[Trend]) -> Path:
        """
        保存缓存文件
        
        Args:
            source_id: 数据源ID
            items: 热搜条目列表
            
        Returns:
            保存的文件路径
        """
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        filename = now.strftime("%Y%m%d_%H%M") + ".json"
        file_path = self.base_path / source_id / filename

        cache_data = CacheData(
            source=source_id,
            timestamp=timestamp,
            items=items,
        )

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            data_dict = omit_empty(asdict(cache_data))
            json.dump(data_dict, f, ensure_ascii=False, indent=2)

        return file_path

    def load(self, source_id: str, date_str: str) -> List[List[Trend]]:
        """
        加载指定日期的缓存数据
        
        Args:
            source_id: 数据源ID
            date_str: 日期字符串 YYYYMMDD
            
        Returns:
            缓存数据列表（每个时间点一个列表）
        """
        source_dir = self.base_path / source_id
        if not source_dir.exists():
            return []

        items_list = []
        for json_file in source_dir.glob(f"{date_str}_*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    items_dict = data.get("items", [])
                    items = [Trend(**item) for item in items_dict]
                    items_list.append(items)
            except Exception:
                continue

        return items_list

    def clear(self, source_id: Optional[str] = None) -> None:
        """
        清除缓存
        
        Args:
            source_id: 数据源ID，为空则清除所有
        """
        import shutil

        if source_id:
            source_dir = self.base_path / source_id
            if source_dir.exists():
                shutil.rmtree(source_dir)
        else:
            for source_dir in self.base_path.iterdir():
                if source_dir.is_dir() and source_dir.name != "summaries":
                    shutil.rmtree(source_dir)
