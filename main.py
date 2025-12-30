"""
August - AI 驱动的每日新闻简报系统

主入口文件
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from src.core import cfg, setup_logger, get_logger
from src.scheduler import scheduled_task
from src.web import render_page, parse_markdown, get_available_dates

# 初始化日志
setup_logger()
logger = get_logger(__name__)

# 定时调度器
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting scheduler...")
    scheduler.add_job(
        scheduled_task,
        "interval",
        minutes=30,
        id="fetch_and_aggregate",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: fetch and aggregate every 30 minutes")

    logger.info("Running initial fetch and aggregate...")
    asyncio.create_task(scheduled_task())

    yield

    logger.info("Stopping scheduler...")
    scheduler.shutdown()


# FastAPI 应用
app = FastAPI(
    title="August - AI 驱动的每日简报",
    description="聚合多个数据源的热搜新闻，提供 AI 摘要和分析",
    version="1.0.0",
    lifespan=lifespan
)


# ==================== 页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index(date: str | None = Query(None, description="日期，格式：YYYY-MM-DD")):
    """首页 - 展示指定日期的热搜数据"""
    try:
        html_content = render_page(date)
        return HTMLResponse(content=html_content)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ==================== API 路由 ====================

@app.get("/api/news/{date}")
async def get_news_data(date: str):
    """获取指定日期的新闻数据"""
    available_dates = get_available_dates()
    if date not in available_dates:
        raise HTTPException(status_code=404, detail=f"未找到 {date} 的数据")

    try:
        parsed = parse_markdown(date)
        all_news = []
        for source in parsed.get("sources", []):
            source_name = source.get("name", "")
            for item in source.get("items", []):
                all_news.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "source_name": source_name,
                    "rank": item.get("rank", 0)
                })

        return JSONResponse(content={
            "success": True,
            "date": date,
            "news": all_news,
            "total": len(all_news)
        })
    except Exception as e:
        logger.error(f"获取新闻数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@app.get("/api/summary/{date}")
async def get_summary(date: str):
    """获取指定日期的摘要数据"""
    summary_file = cfg.summaries_dir / f"{date}.json"
    if not summary_file.exists():
        raise HTTPException(status_code=404, detail=f"未找到 {date} 的摘要数据")

    try:
        with open(summary_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取摘要数据失败: {str(e)}")


# ==================== 摘要生成 API ====================

class GenerateSummaryRequest(BaseModel):
    """生成摘要请求"""
    news_list: List[dict]
    page: int = 1
    page_size: int = 10


@app.post("/api/summary/generate")
async def generate_summary_on_demand(request: GenerateSummaryRequest):
    """按需生成摘要 - 支持分页"""
    from src.analysis import summary_cache, generate_summaries

    date = datetime.now().strftime("%Y-%m-%d")

    # 检查热搜锚点
    anchor_valid = summary_cache.check_anchor(date, request.news_list)

    if not anchor_valid:
        summary_cache.invalidate_cache_for_date(date)
        summary_cache.update_anchor(date, request.news_list)

    # 分页处理
    start_idx = (request.page - 1) * request.page_size
    end_idx = start_idx + request.page_size
    page_news = request.news_list[start_idx:end_idx]

    if not page_news:
        return JSONResponse(content={
            "success": True,
            "page": request.page,
            "summaries": [],
            "has_more": False,
            "anchor": summary_cache.compute_news_anchor(request.news_list)
        })

    results = []
    to_generate = []

    # 检查缓存
    for news in page_news:
        news_id = news.get("url") or news.get("link", "")
        cached = summary_cache.get_summary(news_id, news.get("title", ""))
        if cached:
            results.append(cached)
        else:
            to_generate.append(news)

    # 生成未缓存的摘要
    if to_generate:
        try:
            news_for_summary = [
                {
                    "title": n.get("title", ""),
                    "url": n.get("url") or n.get("link", ""),
                    "source_name": n.get("source_name") or n.get("source", ""),
                    "markdown_content": None
                }
                for n in to_generate
            ]

            generated = await generate_summaries(news_for_summary)

            new_summaries = []
            for item in generated:
                summary_item = {
                    "news_id": item["url"],
                    "title": item["title"],
                    "url": item["url"],
                    "source_name": item.get("source_name", ""),
                    "summary": item.get("summary", ""),
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                new_summaries.append(summary_item)
                results.append(summary_item)

            if new_summaries:
                summary_cache.save_summaries(date, new_summaries)

        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            for n in to_generate:
                results.append({
                    "news_id": n.get("url") or n.get("link", ""),
                    "title": n.get("title", ""),
                    "url": n.get("url") or n.get("link", ""),
                    "source_name": n.get("source_name") or n.get("source", ""),
                    "summary": "摘要生成失败，请稍后重试。",
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

    # 按原始顺序排序
    url_to_result = {r["url"]: r for r in results}
    ordered_results = []
    for news in page_news:
        url = news.get("url") or news.get("link", "")
        if url in url_to_result:
            ordered_results.append(url_to_result[url])

    has_more = end_idx < len(request.news_list)

    return JSONResponse(content={
        "success": True,
        "page": request.page,
        "total": len(request.news_list),
        "page_size": request.page_size,
        "summaries": ordered_results,
        "has_more": has_more,
        "anchor": summary_cache.compute_news_anchor(request.news_list),
        "cached_count": len(results) - len(to_generate)
    })


# ==================== 分析 API ====================

class AnalyzeNewsRequest(BaseModel):
    """分析新闻请求"""
    news_list: List[dict]


@app.post("/api/analytics/analyze")
async def analyze_news_endpoint(request: AnalyzeNewsRequest):
    """综合分析新闻数据"""
    from src.analysis import analyze_news_data

    try:
        result = await analyze_news_data(request.news_list)
        return JSONResponse(content={
            "success": True,
            **result
        })
    except Exception as e:
        logger.error(f"新闻分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


# ==================== 入口 ====================

def main():
    """启动服务器"""
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
