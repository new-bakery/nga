import logging
import json
from celery import Celery, shared_task, current_app
from celery.exceptions import MaxRetriesExceededError
import asyncio
from bson import ObjectId

from util.json_encoder import copy_without_control_keys
from util.tokenizer import get_token_count
from celery_app import worker
from ._shared import update_source_status
from database import get_pgdb, get_mgdb
from config import config

logger = logging.getLogger()


async def statistics(source_id: int):
    # task = task_statistics.apply_async(args=[source_id])  # 启动 Celery 任务
    task = task_statistics.delay(source_id)  # 启动 Celery 任务
    # await run_statistics(source_id)  # If you want to run it directly, call this
    logger.info(f'celery task statistics {task.id} started for source {source_id}')
    return task


@shared_task(bind=True)
def task_statistics(self, source_id: int):
    logger.info(f'celery task statistics {self.request.id} started for source {source_id}')
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(run_statistics(source_id))
        # return await run_statistics(source_id)
    except Exception as ex:
        logger.error(ex)
        raise


async def run_statistics(source_id: int):
    
    try:
        logger.info(f'calculating statistics for source {source_id}')
        db_source = await update_source_status(source_id, {"statistics": {"status": "running"}})
        doc_id = db_source.doc_id
        if not doc_id:
            raise Exception("Failed to fetch source data")
        async for mgdb in get_mgdb():
            schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
            doc = await schema_collection.find_one({"_id": ObjectId(doc_id)})
        if not doc:
            raise Exception("Failed to fetch source doc")
        
        source_name = doc["source_name"]
        statistics = {}
        tables_count = len(doc["tables"])
        columns_counts = []
        tokens_counts = []

        for table_schema in doc["tables"]:
            table_name = table_schema["table_name"]
            table_statistics = {}
            columns_counts.append(len(table_schema["columns"]))

            cp_table_schema = copy_without_control_keys(table_schema)
            text = json.dumps(cp_table_schema)
            tokens_count = get_token_count(text)
            tokens_counts.append(tokens_count)
            table_statistics["tokens_count"] = tokens_count
            
            table_schema["_statistics"] = table_statistics

        columns_counts.sort()
        mid = len(columns_counts) // 2
        if len(columns_counts) % 2 == 0:
            med_columns_count_per_table = (columns_counts[mid - 1] + columns_counts[mid]) / 2
        else:
            med_columns_count_per_table = columns_counts[mid]

        tokens_counts.sort()
        mid = len(tokens_counts) // 2
        if len(tokens_counts) % 2 == 0:
            med_tokens_count_per_table = (tokens_counts[mid - 1] + tokens_counts[mid]) / 2
        else:
            med_tokens_count_per_table = tokens_counts[mid]

        statistics["tables_count"] = tables_count
        avg_columns_count_per_table = sum(columns_counts) / tables_count
        avg_tokens_count_per_table = sum(tokens_counts) / tables_count
        statistics["tokens_count"] = sum(tokens_counts)
        statistics["avg_columns_count_per_table"] = avg_columns_count_per_table
        statistics["med_columns_count_per_table"] = med_columns_count_per_table
        statistics["avg_tokens_count_per_table"] = avg_tokens_count_per_table
        statistics["med_tokens_count_per_table"] = med_tokens_count_per_table

        
        doc["_statistics"] = statistics
        
        async for mgdb in get_mgdb():
            schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
            doc = await schema_collection.update_one({"_id": ObjectId(doc_id)}, {'$set': doc})
            
        db_source = await update_source_status(source_id,  {"statistics": {"status": "done"}})
        
    except Exception as ex:
        await update_source_status(source_id,   {"statistics": {"status": "failed", "error": str(ex)}})
        logger.error(ex)
        raise

        
    