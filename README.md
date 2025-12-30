# August - AI 驱动的每日新闻简报系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

> Your daily brief, powered by AI  
> AI 驱动的每日简报 - 热点·摘要·分析

## 📖 简介

August 是一个智能新闻聚合系统，自动从多个热门新闻源获取热点资讯，并使用 AI 生成摘要和深度分析。系统支持定时自动更新、多数据源聚合、AI 摘要生成和新闻分析等功能。

### ✨ 主要功能

- 🔄 **多数据源聚合** - 支持 8 个主流新闻源
- 🤖 **AI 摘要生成** - 使用 LLM（GLM-4-Flash）自动生成新闻摘要
- 📊 **新闻分析** - 热点聚类、趋势分析、关键词提取、命名实体识别
- ⏰ **定时更新** - 每 30 分钟自动抓取并聚合最新热搜
- 🌐 **Web 界面** - 简洁的网页展示界面
- 🌍 **彭博社翻译** - 自动将英文新闻翻译为中文

![Dashboard](docs/screenshots/dashboard.png)

## 🚀 快速开始

### 环境要求

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) 包管理器（推荐）
- LLM API 密钥（默认使用智谱 GLM-4-Flash）

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/august.git
cd august
```

#### 2. 安装依赖

使用 uv（推荐）：
```bash
uv sync
```

或使用 pip：
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -e .
```

#### 3. 配置环境变量

复制示例配置文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 密钥：

```env
# LLM 配置
LLM_MODEL=glm-4-flash
LLM_API_KEY=your_api_key_here
LLM_API_BASE=https://open.bigmodel.cn/api/paas/v4
```

支持的 LLM 提供商：
| 提供商 | 模型示例 | API Base |
|--------|----------|----------|
| 智谱 AI | `glm-4-flash` | `https://open.bigmodel.cn/api/paas/v4` |
| OpenAI | `gpt-4o-mini` | `https://api.openai.com/v1/` |
| DeepSeek | `deepseek-chat` | `https://api.deepseek.com/` |

#### 4. 启动服务

```bash
uv run main.py
# 或
python main.py
```

服务启动后访问：**http://127.0.0.1:8000**

## 📁 项目结构

```
august/
├── main.py                 # 主入口 - FastAPI 应用
├── pyproject.toml          # 项目配置和依赖
├── .env                    # 环境变量配置
├── .env.example            # 环境变量示例
│
├── src/                    # 源代码目录
│   ├── core/               # 核心模块
│   │   ├── config.py       # 配置管理
│   │   └── logger.py       # 日志系统
│   │
│   ├── fetchers/           # 数据抓取模块
│   │   ├── base.py         # 抓取器基类
│   │   ├── registry.py     # 抓取器注册表
│   │   ├── models.py       # 数据模型
│   │   └── sources/        # 各数据源实现
│   │       ├── baidu.py    # 百度热搜
│   │       ├── bloomberg.py # 彭博社（含翻译）
│   │       ├── cailian.py  # 财联社
│   │       ├── ifeng.py    # 凤凰新闻
│   │       ├── jin10.py    # 金十数据
│   │       ├── jiqizhixin.py # 机器之心
│   │       ├── toutiao.py  # 今日头条
│   │       └── wallstreetcn.py # 华尔街见闻
│   │
│   ├── storage/            # 存储模块
│   │   ├── cache.py        # 数据缓存
│   │   └── aggregator.py   # 每日聚合器
│   │
│   ├── analysis/           # AI 分析模块
│   │   ├── llm.py          # LLM 调用封装
│   │   ├── analyzer.py     # 新闻分析器
│   │   └── cache.py        # 摘要缓存
│   │
│   ├── web/                # Web 模块
│   │   ├── render.py       # 页面渲染
│   │   └── templates/      # HTML 模板
│   │
│   └── scheduler.py        # 定时任务调度
│
├── data/                   # 数据存储目录
│   ├── cache/              # 抓取数据缓存
│   ├── daily/              # 每日聚合文件
│   └── summaries/          # AI 摘要文件
│
└── temp/                   # 临时文件目录
```

## 🔌 支持的数据源

| 数据源 | 标识 | 类型 | 描述 |
|--------|------|------|------|
| 财联社 | cailian | 财经 | 财经快讯 |
| 华尔街见闻 | wallstreetcn | 财经 | 财经资讯 |
| 百度热搜 | baidu | 综合 | 综合热搜 |
| 今日头条 | toutiao | 综合 | 综合热搜 |
| 金十数据 | jin10 | 财经 | 财经快讯 |
| 凤凰新闻 | ifeng | 综合 | 综合新闻 |
| 彭博社 | bloomberg | 国际 | 国际财经（自动翻译） |
| 机器之心 | jiqizhixin | 科技 | AI/科技资讯 |

## 🔧 开发指南

### 添加新数据源

1. 在 `src/fetchers/sources/` 创建新文件，例如 `newsite.py`

2. 继承 `BaseFetcher` 并实现 `fetch` 方法：

```python
from src.fetchers.base import BaseFetcher
from src.fetchers.models import Trend

class NewSiteFetcher(BaseFetcher):
    @classmethod
    def source_name(cls) -> str:
        return "newsite"
    
    async def fetch(self) -> list[Trend]:
        # 实现抓取逻辑
        return [
            Trend(
                rank=1,
                title="新闻标题",
                link="https://example.com/news"
            )
        ]
```

3. 在 `src/fetchers/sources/__init__.py` 导入新抓取器

4. 在 `src/storage/aggregator.py` 的 `SOURCES_CONFIG` 添加配置

### 运行测试

```bash
# 测试单个数据源
uv run python -c "
import asyncio
from src.fetchers import registry

async def test():
    fetcher = registry.get('baidu')()
    trends = await fetcher.fetch()
    for t in trends[:5]:
        print(f'{t.rank}. {t.title}')

asyncio.run(test())
"
```

## 📝 更新日志

### v1.0.0
- 🎉 首次发布
- ✅ 8 个数据源支持
- ✅ AI 摘要生成
- ✅ 新闻分析功能
- ✅ 彭博社翻译
- ✅ 定时自动更新

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

本项目采用 [MIT 许可证](LICENSE)。

## ⚠️ Disclaimer

This project is for educational and research purposes only. You must comply with applicable terms of service and robots.txt rules. If commercial use impacts target websites, violates their policies, or triggers legal disputes, all consequences shall be borne by you. The author bears no responsibility.

本项目仅用于学习和研究目的，请遵守相关条款和 robots.txt 规则。若商业化使用对目标网站造成影响、违反其政策或引发法律纠纷，所有后果由使用者自行承担，与作者无关。

---

<p align="center">Made with ❤️</p>
