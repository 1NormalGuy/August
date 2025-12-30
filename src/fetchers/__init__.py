"""数据抓取模块"""

from .base import BaseFetcher
from .models import Trend
from .registry import FetcherRegistry
from .sources import (
    BaiduFetcher,
    BloombergFetcher,
    CailianFetcher,
    IfengFetcher,
    Jin10Fetcher,
    JiqizhixinFetcher,
    ToutiaoFetcher,
    WallstreetcnFetcher,
)

# 自动注册所有抓取器
FetcherRegistry.register(CailianFetcher())
FetcherRegistry.register(WallstreetcnFetcher())
FetcherRegistry.register(BaiduFetcher())
FetcherRegistry.register(Jin10Fetcher())
FetcherRegistry.register(IfengFetcher())
FetcherRegistry.register(ToutiaoFetcher())
FetcherRegistry.register(BloombergFetcher())
FetcherRegistry.register(JiqizhixinFetcher())

__all__ = [
    "BaseFetcher",
    "Trend",
    "FetcherRegistry",
    "BaiduFetcher",
    "BloombergFetcher",
    "CailianFetcher",
    "IfengFetcher",
    "Jin10Fetcher",
    "JiqizhixinFetcher",
    "ToutiaoFetcher",
    "WallstreetcnFetcher",
]
