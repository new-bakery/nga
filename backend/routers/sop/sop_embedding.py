
import logging
import redis
import numpy as np
from redis.commands.search.query import Query

from schemas.sop import SOP
import dify
from config import config


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
from redis.commands.search.field import TagField, TextField, VectorField, NumericField
import struct
import json

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
            TextField("id"), # This is sop_doc_id
            TagField("sop_doc_id"),
            TagField("category"),
            TagField("is_disabled"),
            TextField("metadata"),
            VectorField(
                name="embedding_sop",
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
            "sop_doc_id": metadata.get("sop_doc_id", ""),
            "category" : metadata.get("category", ""),
            "is_disabled": str(metadata.get("is_disabled", False)).lower(),
            "embedding_sop": binary_vector,
            "metadata": json.dumps(metadata)
        }
    )
    
    
def get_embedding_candidates(sops : list[SOP]) -> list[dict]:
    candidates = []
    for i, sop in enumerate(sops):
        sop_doc_id = sop.id
        id = f"{sop_doc_id}_{i}"
        is_disabled = str(sop.is_disabled).lower()
        
        text = sop.title + sop.description 
        candidates.append({"id": id, "sop_doc_id": sop_doc_id, "category": "sop", "text": text, "is_disabled": is_disabled})
        
        for j, step in enumerate(sop.steps):
            text = step.title + step.description + step.action
            if step.examples:
                for example in step.examples:
                    text += example
            candidates.append({"id": f"{id}_{j}", "sop_doc_id": sop_doc_id, "category": "step", "text": text, "is_disabled": is_disabled})
        
        for k, analysis_guideline in enumerate(sop.analysis_guidelines):
            text = analysis_guideline.title + analysis_guideline.condition + analysis_guideline.action
            if analysis_guideline.reference_data:
                for reference_data in analysis_guideline.reference_data:
                    text += reference_data
            candidates.append({"id": f"{id}_{k}", "sop_doc_id": sop_doc_id,"category": "analysis_guideline", "text": text, "is_disabled": is_disabled})
            
    return candidates

def embedding_candidates(candidates: list[dict]):
    cnt = 0
    results = []
    for candidate in candidates:
        cnt += 1
        id = candidate['id']
        sop_doc_id = candidate['sop_doc_id']
        category = candidate['category']
        is_disabled = candidate['is_disabled']
        text = candidate['text']
        logger.info(f'{cnt}/{len(candidates)} - embedding [{sop_doc_id}]: {text}')
        inputs = {
            "text": text
        }
        res = dify.call_dify(config.DIFY_WORKFLOW_ENDPOINT, config.DIFY_EMBEDDING_APP_KEY, inputs = inputs)
        data = res.get('data', {})
        status = data.get('status', '') 
        if status == 'succeeded':
            result = data['outputs']['result'][0]
            model = result['model']
            dimension = result['dimension']
            embedding = result['embedding']
            results.append((id, sop_doc_id, category, is_disabled, candidate, text, embedding))
        else:
            error_message = f"dify api error {data.get('error', 'unkonwn error')}"
            logger.error(error_message)
            raise Exception(error_message)
    return results


def embedding_sops(sops: list[SOP]):

    redis_client = redis.StrictRedis.from_url(config.REDIS_CONNECTION_STRING, decode_responses=False)
    create_redis_index(redis_client, config.REDIS_SOP_INDEX_NAME, 1024, HNSW, COSINE)

    for sop in sops:
        sop_doc_id = sop.id
        result = redis_client.ft(config.REDIS_SOP_INDEX_NAME).search(f'@sop_doc_id:{{{sop_doc_id}}}')
        if result.docs:
            doc_ids = [doc.id for doc in result.docs]
            redis_client.delete(*doc_ids)

    candidates = get_embedding_candidates(sops)
    results = embedding_candidates(candidates)
    
    for id, sop_doc_id, category, is_disabled, candidate, text, vector in results:
        metadata={
            "sop_doc_id" : sop_doc_id,
            "category": category,
            "is_disabled": is_disabled,
            "text": text
        }
        add_vector_to_redis(redis_client, config.REDIS_SOP_INDEX_NAME, id, vector, metadata)

        
def remove_redis(sop_doc_id):
    def delete_vector_from_redis(redis_client, index_name: str, id: str):
        key = f"{index_name}:{id}"
        if redis_client.exists(key):
            redis_client.delete(key)  # 删除整个键

    redis_client = redis.StrictRedis.from_url(config.REDIS_CONNECTION_STRING, decode_responses=False)
    index_name = config.REDIS_SOP_INDEX_NAME
    delete_vector_from_redis(redis_client, index_name, sop_doc_id)
    


# def search_sop(query: str, top_k: int = 10):
#     inputs = {
#         "text": query
#     }
#     query_vector = None
#     res = dify.call_dify(config.DIFY_WORKFLOW_ENDPOINT, config.DIFY_EMBEDDING_APP_KEY, inputs = inputs)
#     data = res.get('data', {})
#     status = data.get('status', '') 
#     if status == 'succeeded':
#         result = data['outputs']['result'][0]
#         model = result['model']
#         dimension = result['dimension']
#         embedding = result['embedding']
#         query_vector = result
#     else:
#         error_message = f"dify api error {data.get('error', 'unkonwn error')}"
#         logger.error(error_message)
#         raise Exception(error_message)
    
#     if query_vector:
#         vector_buffer = np.array(query_vector, dtype=np.float32).tobytes()
#         filter = f"@{'is_disabled'}:{{{str(False).lower()}}}"
#         query = (
#             Query(f"({filter})=>[KNN {P} @embedding $query_embedding AS vector_score]")
#             .return_fields("sop_doc_id", "metadata", "vector_score")
#             .dialect(2)
#         )
#         redis_client = redis.StrictRedis.from_url(config.REDIS_CONNECTION_STRING, decode_responses=False)
#         result = redis_client.ft(config.REDIS_SOP_INDEX_NAME).search(
#             query, query_params={"query_embedding": vector_buffer}
#         )
#         sop_doc_ids = [doc["sop_doc_id"] for doc in result.docs]
        