"""摘要缓存管理"""

import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.core import cfg

logger = logging.getLogger(__name__)


class SummaryCache:
    """摘要缓存管理器 - 支持基于热搜锚点的缓存失效"""

    def __init__(self):
        self.cache_dir = cfg.summaries_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "index.json"
        self.anchor_file = self.cache_dir / "anchor.json"
        self._load_index()
        self._load_anchor()

    def _load_index(self):
        """加载索引文件"""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.index = json.load(f)
            except Exception as e:
                logger.error(f"加载索引失败: {e}")
                self.index = {}
        else:
            self.index = {}

    def _load_anchor(self):
        """加载锚点文件"""
        if self.anchor_file.exists():
            try:
                with open(self.anchor_file, "r", encoding="utf-8") as f:
                    self.anchor = json.load(f)
            except Exception as e:
                logger.error(f"加载锚点失败: {e}")
                self.anchor = {}
        else:
            self.anchor = {}

    def _save_index(self):
        """保存索引文件"""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存索引失败: {e}")

    def _save_anchor(self):
        """保存锚点文件"""
        try:
            with open(self.anchor_file, "w", encoding="utf-8") as f:
                json.dump(self.anchor, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存锚点失败: {e}")

    def compute_news_anchor(self, news_list: List[Dict]) -> str:
        """计算热搜列表的锚点哈希值"""
        titles = [n.get("title", "") for n in news_list[:50]]
        combined = "|".join(sorted(titles))
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def check_anchor(self, date: str, news_list: List[Dict]) -> bool:
        """
        检查热搜锚点是否匹配
        
        Returns:
            True - 热搜未更新，可以使用缓存
            False - 热搜已更新，需要重新生成摘要
        """
        current_anchor = self.compute_news_anchor(news_list)
        stored_anchor = self.anchor.get(date, {}).get("hash", "")

        if stored_anchor == current_anchor:
            logger.info(f"热搜锚点匹配 (date={date}, anchor={current_anchor})")
            return True
        else:
            logger.info(f"热搜已更新 (date={date}, old={stored_anchor}, new={current_anchor})")
            return False

    def update_anchor(self, date: str, news_list: List[Dict]):
        """更新热搜锚点"""
        anchor_hash = self.compute_news_anchor(news_list)
        self.anchor[date] = {
            "hash": anchor_hash,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "news_count": len(news_list)
        }
        self._save_anchor()
        logger.info(f"更新热搜锚点: date={date}, hash={anchor_hash}")

    def invalidate_cache_for_date(self, date: str):
        """使指定日期的所有缓存失效"""
        keys_to_remove = []
        for key, info in self.index.items():
            if info.get("date") == date:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.index[key]

        if keys_to_remove:
            self._save_index()
            logger.info(f"已清除 {date} 的 {len(keys_to_remove)} 条缓存")

    def _generate_cache_key(self, news_id: str) -> str:
        """生成缓存键"""
        return hashlib.md5(news_id.encode()).hexdigest()[:12]

    def get_summary(self, news_id: str, title: str) -> Optional[Dict]:
        """获取新闻摘要（如果已缓存）"""
        cache_key = self._generate_cache_key(news_id)

        if cache_key in self.index:
            cache_info = self.index[cache_key]
            cache_file = self.cache_dir / cache_info["file"]

            if cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for item in data.get("summaries", []):
                            if item.get("news_id") == news_id:
                                return item
                except Exception as e:
                    logger.error(f"读取缓存失败: {e}")

        return None

    def save_summaries(self, date: str, summaries: List[Dict]) -> str:
        """保存一批摘要"""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{date}_{timestamp}.json"
        cache_file = self.cache_dir / filename

        data = {
            "date": date,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(summaries),
            "summaries": summaries
        }

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            for summary in summaries:
                news_id = summary.get("news_id", summary.get("url", ""))
                cache_key = self._generate_cache_key(news_id)
                self.index[cache_key] = {
                    "file": filename,
                    "title": summary.get("title", ""),
                    "date": date,
                    "timestamp": timestamp
                }

            self._save_index()
            logger.info(f"保存 {len(summaries)} 条摘要到 {filename}")

            return filename

        except Exception as e:
            logger.error(f"保存摘要失败: {e}")
            return ""

    def has_summary(self, news_id: str) -> bool:
        """检查是否已有缓存的摘要"""
        cache_key = self._generate_cache_key(news_id)
        return cache_key in self.index


# 全局缓存实例
summary_cache = SummaryCache()
