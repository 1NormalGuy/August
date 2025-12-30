"""应用配置管理"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent


@dataclass
class Config:
    """应用配置类"""

    # 摘要生成开关
    enable_summary: bool

    # Reader API 配置
    reader_api_endpoint: str
    reader_api_key: str

    # LLM 配置
    llm_api_key: str
    llm_model: str
    llm_api_base: str

    # 路径配置
    data_dir: Path
    summaries_dir: Path
    audio_dir: Path
    temp_dir: Path

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置"""
        return cls(
            enable_summary=os.getenv("ENABLE_SUMMARY", "0") == "1",
            reader_api_endpoint=os.getenv(
                "READER_API_ENDPOINT", "https://api.shuyanai.com/v1/reader"
            ),
            reader_api_key=os.getenv("READER_API_KEY", ""),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_model=os.getenv("LLM_MODEL", "glm-4-flash"),
            llm_api_base=os.getenv("LLM_API_BASE", ""),
            data_dir=ROOT_DIR / "data",
            summaries_dir=ROOT_DIR / "data" / "summaries",
            audio_dir=ROOT_DIR / "data" / "audio",
            temp_dir=ROOT_DIR / "temp",
        )

    def ensure_dirs(self) -> None:
        """确保所有必要目录存在"""
        for dir_path in [self.data_dir, self.summaries_dir, self.audio_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


# 全局配置实例
cfg = Config.from_env()
cfg.ensure_dirs()
