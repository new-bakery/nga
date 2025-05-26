
import logging
import redis
from redis.commands.search.field import TagField, TextField, VectorField, NumericField
import struct
import json
from celery import Celery, shared_task, current_app
from celery.exceptions import MaxRetriesExceededError
import asyncio
from bson import ObjectId

import dify
from config import config
from celery_app import worker
from ._shared import update_source_status
from database import get_pgdb, get_mgdb

# 定义构建索引时的搜索宽度。
# 默认值为 200，增加此值可以提升索引构建精度，但会显著增加索引构建时间和内存占用。
EF_CONSTRUCTION = 200 

# 定义每个节点的连接数（即图的稀疏程度）。
# 默认值为 16，增大此值可以提高搜索精度，但会增加内存使用。
M = 16

FLAT = "FLAT" # 线性搜索
HNSW = "HNSW" # Hierarchical Navigable Small World

IP = "IP" #内积。
COSINE = "COSINE" # 余弦相似度。
L2 = "L2" # L2 欧几里得距离

logger = logging.getLogger()

def create_redis_index(redis_client, index_name: str, vector_dim: int, index_type: str = HNSW, similarity_type: str = COSINE):
    try:
        redis_client.ft(index_name).info()
    except redis.exceptions.ResponseError:
        options = {
            "TYPE": "FLOAT32",
            "DIM": vector_dim,
            "DISTANCE_METRIC": similarity_type,
        }
        if index_type == HNSW:
            options.update({
                "EF_CONSTRUCTION": EF_CONSTRUCTION,
                "M": M
            })
        if index_type == FLAT:
            options.update({
                "BLOCK_SIZE" : 1024
            })
        redis_client.ft(index_name).create_index([
            TextField("id"), # TODO: This should be TAG Field as well !
            TagField("source_doc_id"),
            TagField("source_name"),
            TagField("category"),
            TagField("is_disabled"),
            TagField("table_name"),
            TextField("metadata"),
            VectorField(
                name="embedding_schema",
                algorithm=index_type,
                attributes=options
            )
        ])

def add_vector_to_redis(redis_client, index_name: str, id: str, embedding: list[float], metadata: dict):
    binary_vector = struct.pack(f"{len(embedding)}f", *embedding)
    key = f"{index_name}:{id}"
    if redis_client.exists(key):
        redis_client.delete(key)
    redis_client.hset(
        key,
        mapping={
            "id": id,
            "source_doc_id": metadata.get("source_doc_id", ""),
            "source_name": metadata.get("source_name", ""),
            "category": metadata.get("category", ""),
            "is_disabled": str(metadata.get("is_disabled", False)).lower(),
            "table_name": metadata.get("table_name", ""),
            "embedding_schema": binary_vector,
            "metadata": json.dumps(metadata)
        }
    )
    
    
def get_embedding_candidates(database_schema: dict) -> list[dict]:
    candidates = []
    # We do NOT embedding Database Descriptions. It will be used directly into LLM as context, since it's too highlevel.
    for table_schema in database_schema["tables"]:
        table_name = table_schema["table_name"]
        table_description = ' '.join([d["text"] for d in table_schema["description"]])
        input = {
            "text" : f"{table_name} {table_description}"
        }
        candidates.append((table_schema, table_schema, input))
        
        columns = table_schema.get("columns", [])
        for column_schema in columns:
            column_name = column_schema["column_name"]
            column_description = ' '.join([d["text"] for d in column_schema["description"]])
            input = {
                "text" : f"{column_name} {column_description}"
            }
            candidates.append((table_schema, column_schema, input))
    return candidates



def embedding_candidates(candidates : list[tuple]):
    # We do NOT embedding Database Descriptions. It will be used directly into LLM as context, since it's too highlevel.
    cnt = 0
    results = []
    for table_schema, target_schema, candidate in candidates:
        cnt += 1
        table_name = table_schema["table_name"]
        target_name = table_name
        column_name = ''
        if "column_name" in target_schema:
            column_name = target_schema["column_name"]
            target_name = f"{table_name}.{column_name}"
        text = candidate['text'] # Python 3.10 对嵌套f-string表达式不支持
        logger.info(f'{cnt}/{len(candidates)} - embedding [{target_name}]: {text}')
        res = dify.call_dify(config.DIFY_WORKFLOW_ENDPOINT, config.DIFY_EMBEDDING_APP_KEY, inputs = candidate)
        data = res.get('data', {})
        status = data.get('status', '') 
        if status == 'succeeded':
            result = data['outputs']['result'][0]
            model = result['model']
            dimension = result['dimension']
            embedding = result['embedding']
            results.append((table_schema, target_schema, candidate, result))
        else:
            error_message = f"dify api error {data.get('error', 'unkonwn error')}"
            logger.error(error_message)
            raise Exception(error_message)
    return results
    


async def embedding(source_id: int):
    #task = task_embedding.apply_async(args=[source_id])  # 启动 Celery 任务
    task = task_embedding.delay(source_id) 
    # await run_task_embedding(source_id)  # If you want to run it directly, call this
    logger.info(f'celery task embedding {task.id} started')
    return task
    


@shared_task(bind=True)
def task_embedding(self, source_id: int):
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(run_task_embedding(source_id))
    except Exception as ex:
        logger.error(ex)
        raise
    

async def run_task_embedding(source_id: int):
    try:
        db_source = await update_source_status(source_id, {"embedding": {"status": "running"}})
        doc_id = db_source.doc_id
        if not doc_id:
            raise Exception("Failed to fetch source data")
        async for mgdb in get_mgdb():
            schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
            doc = await schema_collection.find_one({"_id": ObjectId(doc_id)})
        if not doc:
            raise Exception("Failed to fetch source doc")
        source_doc_id = doc_id
        source_name = doc['source_name']
        candidates = get_embedding_candidates(doc)
        results = embedding_candidates(candidates)
        
        redis_client = redis.StrictRedis.from_url(config.REDIS_CONNECTION_STRING, decode_responses=False)
        create_redis_index(redis_client, config.REDIS_SCHEMA_INDEX_NAME, 1024, HNSW, COSINE)
        for table_schema, target_schema, candidate, result in results:
            table_name = table_schema['table_name']
            domains = table_schema['domains']
            tags = target_schema['tags']
            column_name = target_schema.get('column_name', '')
            id = f"{source_name}.{table_name}.{column_name}"  # Notice, if column_name is empty, it will end with dot (".")
            metadata = {
                "category": "tables" if "column_name" in target_schema else "columns",
                "source_doc_id": source_doc_id,
                "source_name": source_name,
                "table_name": table_name,
                "column_name": column_name,
                "domains": ','.join(domains),
                "tags": ','.join(tags),
                "is_disabled": False,
            }
            embedding = result['embedding']
            logger.info(f'sending vector to redis for {id}')
            add_vector_to_redis(redis_client, config.REDIS_SCHEMA_INDEX_NAME, id, embedding, metadata)
        await update_source_status(source_id, {"embedding": {"status": "done"}})
    except Exception as ex:
        await update_source_status(source_id, {"embedding": {"status": "failed", "error": str(ex)}})
        logger.error(ex)
        raise
