"""数据模型定义"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Trend:
    """热搜/新闻条目数据模型"""

    id: str
    """唯一标识符（通常是 URL 或哈希）"""

    title: str
    """标题"""

    url: str
    """链接地址"""

    score: Optional[int] = None
    """热度分数"""

    description: Optional[str] = None
    """描述/摘要"""

    def __post_init__(self):
        """数据验证"""
        if not self.id:
            raise ValueError("id 不能为空")
        if not self.title:
            raise ValueError("title 不能为空")
