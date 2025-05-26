from fastapi import APIRouter, Depends, HTTPException, status, Body, File, UploadFile, Form, Request
from fastapi.responses import Response, StreamingResponse
from typing import List
from sqlalchemy import func
from sqlalchemy.future import select
from bson import ObjectId
import json
import io
import os
import datetime
from urllib.parse import quote
import uuid
import asyncio
import logging
import redis

from database import get_pgdb, get_mgdb, AsyncSession
from models import Source, User, Conversation
from ..auth import get_current_user
from schemas import SuccessOrErrorResponse
from schemas.conversation import *
from schemas.source import *
from schemas.user import UserResponse
from config import config
from util.json_encoder import copy_without_control_keys
from .addto_conversation import addto_conversation
import s3_api

import dify


logger = logging.getLogger()

router = APIRouter()

 
@router.get("", response_model=List[ConversationResponse])
async def get_conversations(current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    result = await pgdb.execute(select(Conversation).filter( (Conversation.user_id == current_user.id) ))
    conversations = [ConversationResponse.model_validate(conversation) for conversation in result.scalars().all()]
    if len(conversations) > 0:
        projection = {
            "_id": 0,
            "topic": 1,
        }
        conversation_collection = mgdb[config.CONVERSATION_COLLECTION_NAME]
        for conversation in conversations:
            doc = await conversation_collection.find_one({"_id": ObjectId(conversation.doc_id)}, projection=projection)
            untitled_topic = f"Untitled_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"
            conversation.topic = untitled_topic
            if doc:
                conversation.topic = doc.get('topic', untitled_topic)
    return conversations


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(conversation_id: int, current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    result = await pgdb.execute(select(Conversation).filter( (Conversation.user_id == current_user.id) & (Conversation.id == conversation_id) ))
    db_conversation = result.scalar_one_or_none()
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    detail = ConversationDetailResponse.model_validate(db_conversation)
    conversation_collection = mgdb[config.CONVERSATION_COLLECTION_NAME]
    doc = await conversation_collection.find_one({"_id": ObjectId(db_conversation.doc_id)})
    if doc:
        doc = copy_without_control_keys(doc)
        detail.topic = doc.get('topic', '')
        detail.doc = doc
    return detail
    

@router.get("/{conversation_id}/sources", response_model=List[SourceDetailResponse])
async def get_conversation_sources(conversation_id: int, current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    result = await pgdb.execute(select(Conversation).filter( (Conversation.user_id == current_user.id) & (Conversation.id == conversation_id) ))
    db_conversation = result.scalar_one_or_none()
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    sources = []
    if db_conversation.source_ids:
        schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
        projection = {
                "tables": 0,
        }
        for source_id in db_conversation.source_ids:
            # 只有允许访问的数据源才会返回
            result = await pgdb.execute(select(Source).filter( (Source.id == source_id) & ( (Source.user_id == current_user.id) | (Source.is_private == False) ) ))
            db_source = result.scalar_one_or_none()
            if not db_source:
                raise HTTPException(status_code=404, detail="Source not found or not permitted")
            detail = SourceDetailResponse.model_validate(db_source)
            doc = await schema_collection.find_one({"_id": ObjectId(detail.doc_id)}, projection=projection)
            if doc:
                doc = copy_without_control_keys(doc)
                detail.source_name = doc.get("source_name","")
                detail.connection = doc.get("connection",{})
                detail.description = doc.get("description",[])
                detail.doc = doc
            sources.append(detail)
    return sources


@router.put("/{conversation_id}/sources", response_model=ConversationDetailResponse)
async def update_conversation_sources(conversation_id: int, sources: list[ConversationSourceUpdate], current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    result = await pgdb.execute(select(Conversation).filter( (Conversation.user_id == current_user.id) & (Conversation.id == conversation_id) ))
    db_conversation = result.scalar_one_or_none()
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    for source in sources:
        source_name = source.source_name
        result = await pgdb.execute(select(Source).filter( (Source.id == source.source_id) & ( (Source.user_id == current_user.id) | (Source.is_private == False) ) ))
        db_source = result.scalar_one_or_none()
        if not db_source:
            raise HTTPException(status_code=404, detail=f"Source {source_name} not found or not permitted")
    source_ids = [source.source_id for source in sources]
    db_conversation.source_ids = source_ids
    await pgdb.commit()
    await pgdb.refresh(db_conversation)
    detail = ConversationDetailResponse.model_validate(db_conversation)
    conversation_collection = mgdb[config.CONVERSATION_COLLECTION_NAME]
    doc = await conversation_collection.find_one({"_id": ObjectId(db_conversation.doc_id)})
    if doc:
        doc = copy_without_control_keys(doc)
        detail.topic = doc.get('topic', '')
        detail.doc = doc
    return detail



# @router.put("/{conversation_id}/topic", response_model=ConversationDetailResponse)
# async def update_conversation_topic(conversation_id: int, current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
#     result = await pgdb.execute(select(Conversation).filter( (Conversation.user_id == current_user.id) & (Conversation.id == conversation_id) ))
#     db_conversation = result.scalar_one_or_none()
#     if not db_conversation:
#         raise HTTPException(status_code=404, detail="Conversation not found")
#     conversation_collection = mgdb[config.CONVERSATION_COLLECTION_NAME]
#     projection = {
#         "_id": 0,
#         "topic" : 1
#     }
#     doc = conversation_collection.find_one({"_id": ObjectId(db_conversation.doc_id)}, projection=projection)
#     if doc:
#         inputs = {
#             "conversation_id": db_conversation.doc_id,
#         }
#         res = dify.call_dify(config.DIFY_WORKFLOW_ENDPOINT, config.DIFY_TOPIC_GENERATOR_APP_KEY, inputs = inputs)
#         if res['data']['status'] == 'succeeded':
#             topic = res['data']['outputs']['topic']
#             conversation_collection.update_one({"_id": ObjectId(db_conversation.doc_id)}, {"$set": {"topic": topic}} )
#             detail = ConversationDetailResponse.model_validate(db_conversation)
#             doc = conversation_collection.find_one({"_id": ObjectId(db_conversation.doc_id)})
#             if doc:
#                 doc = copy_without_control_keys(doc)
#                 detail.topic = doc.get('topic', '')
#                 detail.doc = doc
#             return detail
#         else:
#             error_message = f"dify api error {res['data']['error']}"
#             raise Exception(error_message)


# /api/conversations/:id/chat                          POST     # chat with conversation
# this is SSE



@router.post("/{conversation_id}/chat", response_model=ChatTaskResponse)
async def chat_request(conversation_id: int, sources: list[ConversationSourceUpdate], user_request: str, use_sop = False, expire : int = 30, current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    available_sources = []
    for source in sources:
        source_id = source.source_id
        result = await pgdb.execute(select(Source).filter( (Source.id == source_id) & ( (Source.user_id == current_user.id) | (Source.is_private == False) ) ))
        db_source = result.scalar_one_or_none()
        if not db_source:
            raise HTTPException(status_code=404, detail="Source not found or not permitted")
        detail = SourceResponse.model_validate(db_source)
        available_sources.append(detail)

    source_doc_ids = ",".join([source.doc_id for source in available_sources])
    source_ids = [source.id for source in available_sources]
    
    if len(source_doc_ids) == 0:
        raise HTTPException(status_code=404, detail="No sources permitted or available")

    inputs = {
        "source_doc_ids": source_doc_ids,
        "current_request": user_request,
        "use_sop": use_sop,
        "user":   UserResponse.model_validate(current_user).model_dump(),
    }
    if conversation_id < 0:
        conversation_objId = str(ObjectId())  # New Conversation ID
        # 统一时间格式,注意，是App服务器本地时间
        db_conversation = Conversation(user_id=current_user.id, source_ids=source_ids, created_at=datetime.datetime.now().replace(tzinfo=None), doc_id = conversation_objId)
        pgdb.add(db_conversation)
        await pgdb.commit()
        await pgdb.refresh(db_conversation)
        inputs['conversation_id'] = db_conversation.id
        inputs['conversation_doc_id'] = conversation_objId
    else:
        result = await pgdb.execute(select(Conversation).filter( (Conversation.id == conversation_id) ))
        db_conversation = result.scalar_one_or_none()
        if not db_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conversation_objId = db_conversation.doc_id
        inputs['conversation_id'] = db_conversation.id
        inputs['conversation_doc_id'] = conversation_objId
    
    redis_client = redis.StrictRedis.from_url(config.REDIS_CONNECTION_STRING, decode_responses=False)
    chat_id = str(uuid.uuid4())
    inputs['chat_id'] = chat_id
    redis_client.setex(chat_id, 30 if expire < 30 else expire , json.dumps(inputs))  # at least 30 seconds
    
    return ChatTaskResponse(**inputs)
    

from .luna_sse import *

# current_user: User = Depends(get_current_user),

# @router.get("/{chat_id}/lunachat-sse")
# async def chat_response(chat_id: str, pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    
#     async def event_stream(inputs, chat_id):
#         try:
#             ctx = {}
#             events = dify.stream_dify(config.DIFY_WORKFLOW_ENDPOINT, config.DIFY_PLANNER_APP_KEY, inputs = inputs)
#             for event in events:
#                 data = json.loads(event.data)
#                 event = data.get("event")
#                 title = data.get("data", {}).get("title", "")
#                 handler_key = str.lower(f"{event}>{title}")
#                 if handler_key in luna_event_handlers:
#                     result = luna_event_handlers[handler_key](data, ctx)
#                     if result:
#                         result.chat_id = chat_id
#                         yield "data: " + json.dumps(ChatSSEResponse.model_dump(result)) + "\n\n"
#         except asyncio.CancelledError:
#             logger.error("Event stream was cancelled.")
#             raise
#         except Exception as e:
#             logger.error(f"Error in event stream: {e}")
#             raise
#         finally:
#             logger.info("Event stream terminated.")

#     redis_client = redis.StrictRedis.from_url(config.REDIS_CONNECTION_STRING, decode_responses=False)
#     chat_instruction = redis_client.get(chat_id)
#     chat_instruction = json.loads(chat_instruction)
    
#     current_user = chat_instruction.get("user")
    
#     inputs = {
#         "conversation_id" : chat_instruction.get("conversation_doc_id"),
#         "source_doc_ids" : chat_instruction.get("source_doc_ids"),
#         "current_request" : chat_instruction.get("current_request"),
#         "use_sop": str(chat_instruction.get("use_sop")).lower(),
#     }

#     # inputs = {
#     #     "conversation_id" : str(ObjectId()),
#     #     "source_doc_ids" : "67b30f6b04d70354e34eecb0",
#     #     "current_request" : "How many products we sale ?",
#     # }



#     return StreamingResponse(
#         event_stream(inputs, chat_id),
#         media_type="text/event-stream",
#         headers={
#             'Cache-Control': 'no-cache',
#             'Connection': 'keep-alive',
#             'Content-Type': 'text/event-stream',
#             'Access-Control-Allow-Origin': '*',
#         }
#     )


@router.get("/{chat_id}/luna2chat-sse")
async def chat_response2(chat_id: str,  pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    
    async def event_stream(inputs, chat_id):
        try:
            ctx = {}
            tasks = None
            yield "data: " + json.dumps(ChatSSEResponse.model_dump(StartSignal(chat_id))) + "\n\n"
            conversation_id = inputs['conversation_id']
            current_request = inputs['current_request']
            user_request_message = {
                "role": "user", "markdowns": [current_request]
            }
            await addto_conversation(mgdb, conversation_id, user_request_message)
            events = dify.stream_dify(config.DIFY_WORKFLOW_ENDPOINT, config.DIFY_PLANNER2_APP_KEY, inputs = inputs)
            for event in events:
                data = json.loads(event.data)
                event = data.get("event")
                title = data.get("data", {}).get("title", "")
                handler_key = str.lower(f"{event}>{title}")
                if event == dify.EVENT_WORKFLOW_FINISHED:
                   status = data.get("data", {}).get('status', '')
                   if status == "succeeded":
                       tasks = data.get("data", {}).get('outputs', {}).get('plan', '')
                   else:
                       error = data.get("data", {}).get('error', '')
                       yield "data: " + json.dumps(ChatSSEResponse.model_dump(AsError(error, chat_id))) + "\n\n"
                if handler_key in luna2_event_handlers:
                    result = luna2_event_handlers[handler_key](data, ctx)
                    if result:
                        result.chat_id = chat_id
                        yield "data: " + json.dumps(ChatSSEResponse.model_dump(result)) + "\n\n"
            if tasks:
                dependent_data = {}
                for task in tasks:
                    logger.info(f"starting task: {task}")
                    task_id = task.get("task_id")
                    dependent_task_ids = task.get("dependent_task_ids", [])
                    instruction = task.get("instruction")
                    task_type = task.get("task_type")
                    source_id = task.get("source_id")
                    dependent_input_data = []
                    for dependent_task_id in dependent_task_ids:
                        dependent_input_data.append(dependent_data.get(dependent_task_id, {}))
                    if task_type == "sql-agent":
                        inputs = {
                            "conversation_id": conversation_id,
                            "current_request": instruction,
                            "source_doc_id" : source_id,
                        }
                        events = dify.stream_dify(config.DIFY_WORKFLOW_ENDPOINT, config.DIFY_SQL_AGENT_APP_KEY, inputs = inputs)
                        for event in events:
                            data = json.loads(event.data)
                            event = data.get("event")
                            title = data.get("data", {}).get("title", "")
                            handler_key = str.lower(f"{event}>{title}")
                            if event == dify.EVENT_WORKFLOW_FINISHED:
                                status = data.get("data", {}).get('status', '')
                                if status == "succeeded":
                                    outputs = data.get("data", {}).get('outputs', {})
                                    await addto_conversation(mgdb, conversation_id, outputs)
                                    logger.info(f"sql-agent outputs: {outputs}")
                                    dependent_data[task_id] = outputs["jsons"] # Save Data for dependent tasks
                                else:
                                    error = data.get("data", {}).get('error', '')
                                    yield "data: " + json.dumps(ChatSSEResponse.model_dump(AsError(error, chat_id))) + "\n\n"
                            if handler_key in sqlagent_event_handlers:
                                result = sqlagent_event_handlers[handler_key](data, ctx)
                                if result:
                                    result.chat_id = chat_id
                                    yield "data: " + json.dumps(ChatSSEResponse.model_dump(result)) + "\n\n"
                    elif task_type == "chat-agent":
                        inputs = {
                            "conversation_id": conversation_id,
                            "current_request": instruction,
                        }
                        events = dify.stream_dify(config.DIFY_WORKFLOW_ENDPOINT, config.DIFY_CHAT_AGENT_APP_KEY, inputs = inputs)
                        for event in events:
                            data = json.loads(event.data)
                            event = data.get("event")
                            title = data.get("data", {}).get("title", "")
                            handler_key = str.lower(f"{event}>{title}")
                            if event == dify.EVENT_WORKFLOW_FINISHED:
                                status = data.get("data", {}).get('status', '')
                                if status == "succeeded":
                                    outputs = data.get("data", {}).get('outputs', {})
                                    await addto_conversation(mgdb, conversation_id, outputs)
                                    logger.info(f"chat-agent outputs: {outputs}")
                                else:
                                    error = data.get("data", {}).get('error', '')
                                    yield "data: " + json.dumps(ChatSSEResponse.model_dump(AsError(error, chat_id))) + "\n\n"
                            if handler_key in chatagent_event_handlers:
                                result = chatagent_event_handlers[handler_key](data, ctx)
                                if result:
                                    result.chat_id = chat_id
                                    yield "data: " + json.dumps(ChatSSEResponse.model_dump(result)) + "\n\n"
                    elif task_type == "python-data-agent":
                        inputs = {
                            "data": json.dumps(dependent_input_data),
                            "instruction": instruction,
                        }
                        events = dify.stream_dify(config.DIFY_WORKFLOW_ENDPOINT, config.DIFY_PYTHON_DATA_AGENT_APP_KEY, inputs = inputs)
                        for event in events:
                            data = json.loads(event.data)
                            event = data.get("event")
                            title = data.get("data", {}).get("title", "")
                            handler_key = str.lower(f"{event}>{title}")
                            if event == dify.EVENT_WORKFLOW_FINISHED:
                                status = data.get("data", {}).get('status', '')
                                if status == "succeeded":
                                    outputs = data.get("data", {}).get('outputs', {})
                                    await addto_conversation(mgdb, conversation_id, outputs)
                                    logger.info(f"python-data-agent outputs: {outputs}")
                                    dependent_data[task_id] = outputs["jsons"] # Save Data for dependent tasks
                                else:
                                    error = data.get("data", {}).get('error', '')
                                    yield "data: " + json.dumps(ChatSSEResponse.model_dump(AsError(error, chat_id))) + "\n\n"
                            if handler_key in python_data_agent_event_handlers:
                                result = python_data_agent_event_handlers[handler_key](data, ctx)
                                if result:
                                    result.chat_id = chat_id
                                    yield "data: " + json.dumps(ChatSSEResponse.model_dump(result)) + "\n\n"
                    elif task_type == "plotly-agent":
                        inputs = {
                            "data": json.dumps(dependent_input_data),
                            "instruction": instruction,
                        }
                        events = dify.stream_dify(config.DIFY_WORKFLOW_ENDPOINT, config.DIFY_PLOTLY_AGENT_APP_KEY, inputs = inputs)
                        for event in events:
                            data = json.loads(event.data)
                            event = data.get("event")
                            title = data.get("data", {}).get("title", "")
                            handler_key = str.lower(f"{event}>{title}")
                            if event == dify.EVENT_WORKFLOW_FINISHED:
                                status = data.get("data", {}).get('status', '')
                                if status == "succeeded":
                                    outputs = data.get("data", {}).get('outputs', {})
                                    thought_process = outputs.get('thought_process', [])
                                    if thought_process and len(thought_process) > 0:
                                        html_encoded = thought_process[0]
                                        compressed_data = base64.b64decode(html_encoded)
                                        input_bytes = zlib.decompress(compressed_data)
                                        restored = input_bytes.decode('utf-8')
                                        
                                        file_obj = io.BytesIO(restored.encode("utf-8"))
                                        r = s3_api.upload_fileobj("plotly", f"{chat_id}_{task_id}.html", file_obj, current_user, "text/html")
                                        object_name = r.get("object_name", "")
                                        object_name = object_name.split('/')[-1]
                                        outputs["thought_process"] = [object_name, restored]
                                        yield "data: " + json.dumps(ChatSSEResponse.model_dump(AsPlot(restored, object_name , chat_id))) + "\n\n"
                                    await addto_conversation(mgdb, conversation_id, outputs)
                                    logger.info(f"plotly-agent outputs: {outputs}")
                                else:
                                    error = data.get("data", {}).get('error', '')
                                    yield "data: " + json.dumps(ChatSSEResponse.model_dump(AsError(error, chat_id))) + "\n\n"
                            if handler_key in plotly_agent_event_handlers:
                                result = plotly_agent_event_handlers[handler_key](data, ctx)
                                if result:
                                    result.chat_id = chat_id
                                    yield "data: " + json.dumps(ChatSSEResponse.model_dump(result)) + "\n\n"
                    else:
                        yield "data: " + json.dumps(ChatSSEResponse.model_dump(AsError(f"Unknown task type: {task_type}", chat_id))) + "\n\n"
            yield "data: " + json.dumps(ChatSSEResponse.model_dump(DoneSignal(chat_id))) + "\n\n"
        except asyncio.CancelledError:
            logger.error("Event stream was cancelled.")
            raise
        except Exception as e:
            logger.error(f"Error in event stream: {e}")
            raise
        finally:
            logger.info("Event stream terminated.")

    redis_client = redis.StrictRedis.from_url(config.REDIS_CONNECTION_STRING, decode_responses=False)
    chat_instruction = redis_client.get(chat_id)
    chat_instruction = json.loads(chat_instruction)
    
    current_user = UserResponse.model_validate(chat_instruction.get("user"))
    
    inputs = {
        "conversation_id" : chat_instruction.get("conversation_doc_id"),
        "source_doc_ids" : chat_instruction.get("source_doc_ids"),
        "current_request" : chat_instruction.get("current_request"),
        "use_sop": str(chat_instruction.get("use_sop")).lower(),
    }

    # inputs = {
    #     "conversation_id" : str(ObjectId()),
    #     "source_doc_ids" : "67b30f6b04d70354e34eecb0",
    #     "current_request" : "How many products we sale ?",
    #     "use_sop" : "true",
    # }

    return StreamingResponse(
        event_stream(inputs, chat_id),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'text/event-stream',
            'Access-Control-Allow-Origin': '*',
        }
    )

