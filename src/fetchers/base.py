"""数据抓取器基类"""

from abc import ABC, abstractmethod
from typing import List

from .models import Trend


class BaseFetcher(ABC):
    """数据抓取器基类"""

    @property
    @abstractmethod
    def source_id(self) -> str:
        """
        数据源唯一标识符
        
        Returns:
            数据源ID字符串
        """
        pass

    @property
    def source_name(self) -> str:
        """
        数据源显示名称
        
        Returns:
            数据源名称
        """
        return self.source_id

    @abstractmethod
    async def fetch(self) -> List[Trend]:
        """
        抓取热搜/新闻数据
        
        Returns:
            Trend 对象列表
        """
        pass
