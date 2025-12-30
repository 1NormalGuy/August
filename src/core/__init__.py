"""核心模块：配置和日志"""

from .config import cfg, Config
from .logger import setup_logger, get_logger

__all__ = ["cfg", "Config", "setup_logger", "get_logger"]
