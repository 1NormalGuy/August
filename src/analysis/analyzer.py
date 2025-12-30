"""新闻分析模块 - 事件聚类、趋势检测、实体抽取"""

import logging
import re
import json
import asyncio
from typing import List, Dict, Any
from collections import Counter

from .llm import invoke_llm

logger = logging.getLogger(__name__)

# 停用词列表
STOP_WORDS = {
    '的', '了', '是', '在', '和', '与', '为', '被', '将', '到', '从', '对', '等',
    '也', '上', '中', '年', '月', '日', '时', '分', '秒', '个', '多', '有', '这',
    '那', '一', '不', '人', '都', '能', '可', '要', '就', '我', '你', '他', '她',
    '它', '们', '或', '但', '如', '而', '去', '来', '过', '下', '更', '最', '很',
    '还', '已', '及', '该', '其', '所', '被', '则', '者', '之', '于', '以', '又',
    '什么', '怎么', '如何', '为什么', '哪里', '谁', '哪个', '几', '多少',
    '一个', '一种', '一些', '这个', '那个', '这些', '那些', '什么样',
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'to', 'of', 'in',
    'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
    'during', 'before', 'after', 'above', 'below', 'between', 'under',
    'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
    'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
    'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until',
}


class NewsAnalyzer:
    """新闻分析器"""

    async def analyze_news(self, news_list: List[Dict]) -> Dict[str, Any]:
        """
        综合分析新闻列表
        
        Returns:
            包含 clusters, trends, entities, timeline, source_stats 的字典
        """
        if not news_list:
            return {
                "clusters": [],
                "trends": [],
                "entities": [],
                "timeline": [],
                "source_stats": {}
            }

        # 并行执行分析任务
        results = await asyncio.gather(
            self._cluster_events(news_list),
            self._detect_trends(news_list),
            self._extract_entities(news_list),
            return_exceptions=True
        )

        clusters = results[0] if not isinstance(results[0], Exception) else []
        trends = results[1] if not isinstance(results[1], Exception) else []
        entities = results[2] if not isinstance(results[2], Exception) else {"entities": [], "timeline": []}

        source_stats = self._compute_source_stats(news_list)

        return {
            "clusters": clusters,
            "trends": trends,
            "entities": entities.get("entities", []),
            "timeline": entities.get("timeline", []),
            "source_stats": source_stats
        }

    async def _cluster_events(self, news_list: List[Dict]) -> List[Dict]:
        """事件聚类 - 将相似新闻归类"""
        if len(news_list) < 3:
            return []

        titles = [f"{i+1}. {n.get('title', '')}" for i, n in enumerate(news_list[:50])]
        titles_text = "\n".join(titles)

        prompt = f"""分析以下新闻标题，将它们按事件主题聚类。每个聚类代表一个独立事件或话题。

新闻标题：
{titles_text}

请返回JSON格式的聚类结果，格式如下：
{{
  "clusters": [
    {{
      "theme": "事件主题名称（简洁，5-15字）",
      "description": "事件简述（1-2句话）",
      "news_ids": [1, 3, 5],
      "importance": "high/medium/low",
      "category": "politics/economy/tech/society/entertainment/sports/international"
    }}
  ]
}}

要求：
1. 只聚类真正相关的新闻，不要强行归类
2. 每个聚类至少包含2条新闻
3. 最多返回8个聚类
4. 按重要性排序（high优先）
5. 直接返回JSON，不要有其他文字"""

        try:
            response = await invoke_llm(prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                clusters = data.get("clusters", [])

                for cluster in clusters:
                    cluster["news"] = []
                    for news_id in cluster.get("news_ids", []):
                        idx = news_id - 1
                        if 0 <= idx < len(news_list):
                            cluster["news"].append({
                                "title": news_list[idx].get("title", ""),
                                "url": news_list[idx].get("url", ""),
                                "source": news_list[idx].get("source_name", "")
                            })

                return clusters
        except Exception as e:
            logger.error(f"事件聚类失败: {e}")

        return []

    async def _detect_trends(self, news_list: List[Dict]) -> List[Dict]:
        """趋势检测 - 识别热点话题"""
        word_freq = Counter()

        for news in news_list:
            title = news.get("title", "")
            for length in range(2, 5):
                for i in range(len(title) - length + 1):
                    word = title[i:i+length]
                    if not re.search(r'[\s\d\W]', word) and word.lower() not in STOP_WORDS:
                        word_freq[word] += 1

        top_words = word_freq.most_common(20)

        if not top_words:
            return []

        words_text = ", ".join([f"{w}({c}次)" for w, c in top_words])

        prompt = f"""基于以下新闻关键词频率，分析当前热点趋势：

高频关键词：{words_text}

请返回JSON格式的趋势分析，格式如下：
{{
  "trends": [
    {{
      "keyword": "关键词",
      "heat": 95,
      "trend": "rising/stable/falling",
      "type": "breaking/ongoing/emerging",
      "summary": "简要说明这个趋势是什么（10-20字）"
    }}
  ]
}}

要求：
1. 选择最有意义的5-8个趋势
2. 合并相似关键词
3. 按热度排序
4. 直接返回JSON"""

        try:
            response = await invoke_llm(prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("trends", [])
        except Exception as e:
            logger.error(f"趋势检测失败: {e}")

        # 降级方案
        return [
            {
                "keyword": word,
                "heat": min(100, count * 10),
                "trend": "stable",
                "type": "ongoing",
                "summary": f"出现{count}次"
            }
            for word, count in top_words[:8]
        ]

    async def _extract_entities(self, news_list: List[Dict]) -> Dict:
        """实体抽取 + 时间线"""
        titles = [n.get("title", "") for n in news_list[:40]]
        titles_text = "\n".join(titles)

        prompt = f"""从以下新闻标题中提取关键实体（人物、组织、地点）和事件时间线：

新闻标题：
{titles_text}

请返回JSON格式，格式如下：
{{
  "entities": [
    {{
      "name": "实体名称",
      "type": "person/org/location/product",
      "mentions": 5,
      "context": "简要说明该实体在新闻中的角色（10字内）"
    }}
  ],
  "timeline": [
    {{
      "event": "事件简述（15字内）",
      "entities": ["相关实体名"],
      "importance": "high/medium/low"
    }}
  ]
}}

要求：
1. entities 最多返回12个重要实体
2. timeline 最多返回6个关键事件
3. 按重要性/提及次数排序
4. 直接返回JSON"""

        try:
            response = await invoke_llm(prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "entities": data.get("entities", []),
                    "timeline": data.get("timeline", [])
                }
        except Exception as e:
            logger.error(f"实体抽取失败: {e}")

        return {"entities": [], "timeline": []}

    def _compute_source_stats(self, news_list: List[Dict]) -> Dict[str, int]:
        """统计来源分布"""
        stats = Counter()
        for news in news_list:
            source = news.get("source_name", "未知")
            stats[source] += 1
        return dict(stats.most_common())


# 全局分析器实例
news_analyzer = NewsAnalyzer()


async def analyze_news_data(news_list: List[Dict]) -> Dict[str, Any]:
    """分析新闻数据的入口函数"""
    return await news_analyzer.analyze_news(news_list)
