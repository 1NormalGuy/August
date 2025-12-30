"""页面渲染模块"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from src.core import cfg

# 模板路径
TEMPLATE_PATH = Path(__file__).parent / "templates" / "trending.html"

# 正则模式
DATE_FILE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
ITEM_LINE_PATTERN = re.compile(r"^(\d+)\.\s+\[(.+?)\]\((.+?)\)")

# 数据源样式配置
SOURCE_PRESENTATION: Dict[str, Dict[str, str]] = {
    "财联社": {"icon": "💰", "color_class": "red"},
    "华尔街见闻": {"icon": "💹", "color_class": "green"},
    "金十数据": {"icon": "📊", "color_class": "cyan"},
    "百度热搜": {"icon": "🔍", "color_class": "blue"},
    "今日头条": {"icon": "📅", "color_class": "orange"},
    "凤凰网": {"icon": "💎", "color_class": "purple"},
    "彭博社": {"icon": "📰", "color_class": "blue"},
    "机器之心": {"icon": "🤖", "color_class": "cyan"},
}


def get_available_dates() -> List[str]:
    """获取所有可用的日期"""
    dates: List[str] = []
    for md_file in cfg.data_dir.glob("*.md"):
        if DATE_FILE_PATTERN.fullmatch(md_file.stem):
            dates.append(md_file.stem)
    return sorted(dates, reverse=True)


def parse_markdown(date_str: str) -> Dict[str, object]:
    """解析 Markdown 文件"""
    md_path = cfg.data_dir / f"{date_str}.md"
    if not md_path.exists():
        raise FileNotFoundError(f"数据文件不存在：{md_path}")

    sources: List[Dict[str, object]] = []
    current: Optional[Dict[str, object]] = None
    title_line: Optional[str] = None

    with md_path.open(encoding="utf-8") as fp:
        for raw_line in fp:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("# "):
                title_line = line.lstrip("# ").strip()
                continue
            if line.startswith("## "):
                source_name = line[3:].strip()
                meta = SOURCE_PRESENTATION.get(
                    source_name,
                    {"icon": "💎", "color_class": "green"},
                )
                current = {"name": source_name, "meta": meta, "items": []}
                sources.append(current)
                continue
            match = ITEM_LINE_PATTERN.match(line)
            if match and current:
                rank = int(match.group(1))
                title = match.group(2).strip()
                link = match.group(3).strip()
                current["items"].append({"rank": rank, "title": title, "link": link})

    return {
        "title": title_line or f"{date_str} 热门资讯",
        "sources": sources,
    }


def render_page(selected_date: Optional[str] = None) -> str:
    """渲染首页"""
    available_dates = get_available_dates()
    if not available_dates:
        raise RuntimeError("data 目录中未找到任何日期文件")

    date_to_use = selected_date or available_dates[0]

    if date_to_use not in available_dates:
        sources: Sequence[Dict[str, object]] = []
    else:
        parsed = parse_markdown(date_to_use)
        sources = parsed["sources"]

    total_items = sum(len(s["items"]) for s in sources)

    data = {
        "selected_date": date_to_use,
        "selected_date_display": date_to_use,
        "sources": sources,
        "source_count": len(sources),
        "item_count": total_items,
        "build_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    json_data = json.dumps(data, ensure_ascii=False, indent=2)
    html_content = template_text.replace("__DATA_PLACEHOLDER__", json_data)

    return html_content
