"""数据抓取器注册器"""

from typing import Dict, List, Optional

from .base import BaseFetcher


class FetcherRegistry:
    """数据抓取器注册表"""

    _fetchers: Dict[str, BaseFetcher] = {}

    @classmethod
    def register(cls, fetcher: BaseFetcher) -> None:
        """
        注册数据抓取器
        
        Args:
            fetcher: 抓取器实例
        """
        cls._fetchers[fetcher.source_id] = fetcher

    @classmethod
    def get(cls, source_id: str) -> BaseFetcher:
        """
        获取指定数据源的抓取器
        
        Args:
            source_id: 数据源ID
            
        Returns:
            抓取器实例
            
        Raises:
            ValueError: 数据源未注册
        """
        if source_id not in cls._fetchers:
            raise ValueError(f"数据源 '{source_id}' 未注册")
        return cls._fetchers[source_id]

    @classmethod
    def get_optional(cls, source_id: str) -> Optional[BaseFetcher]:
        """
        获取指定数据源的抓取器（可选）
        
        Args:
            source_id: 数据源ID
            
        Returns:
            抓取器实例，不存在则返回 None
        """
        return cls._fetchers.get(source_id)

    @classmethod
    def all(cls) -> Dict[str, BaseFetcher]:
        """
        获取所有已注册的抓取器
        
        Returns:
            数据源ID到抓取器的映射
        """
        return cls._fetchers.copy()

    @classmethod
    def list_source_ids(cls) -> List[str]:
        """
        获取所有已注册的数据源ID
        
        Returns:
            数据源ID列表
        """
        return list(cls._fetchers.keys())

    @classmethod
    def count(cls) -> int:
        """
        获取已注册的抓取器数量
        
        Returns:
            抓取器数量
        """
        return len(cls._fetchers)
