"""数据源抓取器"""

from .baidu import BaiduFetcher
from .bloomberg import BloombergFetcher
from .cailian import CailianFetcher
from .ifeng import IfengFetcher
from .jin10 import Jin10Fetcher
from .jiqizhixin import JiqizhixinFetcher
from .toutiao import ToutiaoFetcher
from .wallstreetcn import WallstreetcnFetcher

__all__ = [
    "BaiduFetcher",
    "BloombergFetcher",
    "CailianFetcher",
    "IfengFetcher",
    "Jin10Fetcher",
    "JiqizhixinFetcher",
    "ToutiaoFetcher",
    "WallstreetcnFetcher",
]
