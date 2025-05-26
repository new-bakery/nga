import json
import uuid
import datetime
import redis
import struct
from typing import Any
from redis.commands.search.field import TagField, TextField, VectorField, NumericField
from bson import ObjectId
import logging

from config import config
import dify


logger = logging.getLogger()


FLAT = "FLAT" # 线性搜索
HNSW = "HNSW" # Hierarchical Navigable Small World

IP = "IP" #内积。
COSINE = "COSINE" # 余弦相似度。
L2 = "L2" # L2 欧几里得距离

# 定义构建索引时的搜索宽度。
# 默认值为 200，增加此值可以提升索引构建精度，但会显著增加索引构建时间和内存占用。
EF_CONSTRUCTION = 200 

# 定义每个节点的连接数（即图的稀疏程度）。
# 默认值为 16，增大此值可以提高搜索精度，但会增加内存使用。
M = 16


ID = 'id'





def embedding_text(text: str) -> list[float]:
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
        return embedding
    else:
        error_message = f"dify api error {data.get('error', 'unkonwn error')}"
        logger.error(error_message)
        raise Exception(error_message)

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
            TagField(ID),
            TagField("conversation_id"),
            TagField("message_id"),
            TagField("role"),
            TagField("is_error"),
            TextField("message"),
            VectorField(
                name="embedding_conversation",
                algorithm=index_type,
                attributes=options
            ),
            NumericField("tokens_count"),
        ])
def add_to_redis(conversation_id, message):
    message_id = message["message_id"]
    role = message["role"]
    is_error = message["is_error"]
    embedding = message["embedding_conversation"]
    binary_vector = struct.pack(f"{len(embedding)}f", *embedding)
    key = f"{conversation_id}-{message_id}"

    redis_connection_string = config.REDIS_CONNECTION_STRING
    redis_index_name = config.REDIS_CONVERSATION_INDEX_NAME

    redis_client = redis.StrictRedis.from_url(redis_connection_string)
    create_redis_index(redis_client, redis_index_name, len(embedding))

    if redis_client.exists(key):
        redis_client.delete(key)
    
    redis_client.hset(
        key,
        mapping={
            ID: key,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "role": role,
            "is_error": str(is_error).lower(),
            "embedding_conversation": binary_vector,
            "message": json.dumps(message),
            "tokens_count": 0, # TODO: calculate tokens count
        }
    )

async def add_to_mongodb(mgdb, conversation_id, message):
    
    collection = mgdb[config.CONVERSATION_COLLECTION_NAME]
    conversation = await collection.find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        untitled_topic = f"Untitled_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"
        topic = untitled_topic
        if "markdowns" in message:
            markdowns = message.get("markdowns", [])
            if len(markdowns) > 0:
                topic = markdowns[0]
                if len(str.strip(topic)) == 0:
                    topic = untitled_topic
        if len(topic) == 0:
            topic = untitled_topic
        payload = {
            "_id": ObjectId(conversation_id),
            "topic": topic, 
            "messages":[
                message,
            ],
        }
        await collection.insert_one(payload)
    else:
        await collection.update_one({"_id": ObjectId(conversation_id)}, {"$push": {"messages": message}})


def build_message_markdown(message):
    # NOTICE: This is not for DISPLAY for end users. Its for reference for LLMs or for Embedding
    content = []
    role = message["role"]
    mardkwon_content = '\n'.join(message.get("markdowns", []))
    json_content = '\n'.join([f"```json \n {json.dumps(j)} \n ```" for j in message.get("jsons", [])])
    content.append(f"**{role}:**")
    content.append(mardkwon_content)
    content.append(json_content)
    content.append("\n---\n")
    return '\n'.join(content)


async def addto_conversation(mgdb, conversation_id, message):
    
    if "role" not in message:
        raise Exception(f"Message must contain role field")
    
    if "message_id" not in message:
        message["message_id"] = str(uuid.uuid4())
    if "timestamp" not in message:
        message["timestamp"] = datetime.datetime.now().isoformat(timespec='milliseconds')
    if "is_error" not in message:
        message["is_error"] = False
    elif isinstance(message["is_error"], str):
        message["is_error"] = message["is_error"] == "true"
    if "markdowns" not in message:
        message["markdowns"] = []
    if "embedding_conversation" not in message and not message["is_error"]: # Embedding is for seaching the related messages. Error Messages should not be searchable
        embedding_markdown = build_message_markdown(message)
        if embedding_markdown and len(embedding_markdown) > 0:
            # TODO: Embedding is not working properly. Sometimes, the embedding_markdown is too long, which cause the error !
            # message[EMBEDDING] = self.embedding_text(embedding_markdown, user_id)
            pass
    if "error_message" not in message:
        message["error_message"] = ""
    if "jsons" not in message:
        message["jsons"] = []
    if "thought_process" not in message:
        message["thought_process"] = []
    
    message["conversation_id"] = conversation_id

    if "embedding_conversation" in message: # Only message has embedding can be searchable
        await add_to_redis(conversation_id, message)

    await add_to_mongodb(mgdb, conversation_id, message)

