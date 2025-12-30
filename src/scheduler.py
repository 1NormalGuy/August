"""定时任务调度器"""

import logging
from datetime import datetime

from src.core import cfg
from src.fetchers import FetcherRegistry
from src.storage import CacheStorage, DailyAggregator

logger = logging.getLogger(__name__)


async def fetch_all_sources() -> bool:
    """
    抓取所有数据源
    
    Returns:
        是否至少有一个源成功
    """
    source_ids = FetcherRegistry.list_source_ids()
    logger.info(f"Fetching {len(source_ids)} sources...")

    storage = CacheStorage()
    success_count = 0
    total_items = 0

    for source_id in source_ids:
        try:
            fetcher_instance = FetcherRegistry.get(source_id)
            items = await fetcher_instance.fetch()
            storage.save(source_id, items)
            total_items += len(items)
            success_count += 1
        except Exception as e:
            logger.error(f"❌ {source_id}: {e}")

    logger.info(f"Fetch completed: {success_count}/{len(source_ids)} succeeded, {total_items} items total")
    return success_count > 0


def aggregate_today() -> bool:
    """
    聚合今日数据
    
    Returns:
        是否成功
    """
    today = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"Aggregating data for {today}...")

    try:
        aggregator = DailyAggregator()
        result = aggregator.generate(today)
        if result:
            logger.info(f"✅ Aggregation completed for {today}")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Aggregation failed for {today}: {e}")
        return False


async def scheduled_task():
    """定时任务：抓取 -> 聚合"""
    logger.info("Scheduled task started")

    fetch_success = await fetch_all_sources()

    if fetch_success:
        aggregate_today()
    else:
        logger.warning("Fetch failed, skipping aggregation")

    logger.info("Scheduled task completed")
