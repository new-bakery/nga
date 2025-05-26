from fastapi import APIRouter, Depends, HTTPException, status, Body, File, UploadFile, Form
from fastapi.responses import Response
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

from database import get_pgdb, get_mgdb, AsyncSession
from models import Source, User
from ..auth import get_current_user
from schemas import SuccessOrErrorResponse
from schemas.source import *
from config import config
from source_type_manager import get_source_type_context
import source_type_manager as st_mgr
from util.json_encoder import copy_without_control_keys, get_json
from util.json_diff import apply_changes
from source_types._relationships import DetectApproach
import dify
from s3_api import s3_client, upload_fileobj, download_fileobj
from s3_api import BotoCoreError, NoCredentialsError, EndpointConnectionError, ClientError


router = APIRouter()

@router.get("", response_model=List[SourceResponse])
async def get_sources(current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    result = await pgdb.execute(select(Source).filter( (Source.user_id == current_user.id) | (Source.is_private == False) ))
    sources = [SourceResponse.model_validate(source) for source in result.scalars().all()]
    
    if len(sources) > 0:
        schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
        projection = {
            "_id": 0,
            "source_name": 1,
            "connection": 1,
            "description": 1,
        }
        for source in sources:
           doc = await schema_collection.find_one({"_id": ObjectId(source.doc_id)}, projection=projection)
           if doc:
               source.source_name = doc.get("source_name","")
               source.connection = doc.get("connection",{})
               source.description = doc.get("description",[])
    return sources
    

@router.put("/mark_is_private/{source_id}", response_model=SourceDetailResponse)
async def mark_is_private(source_id: int, is_private: bool, current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    result = await pgdb.execute(select(Source).filter( (Source.id == source_id) & ( (Source.user_id == current_user.id) ) ))
    db_source = result.scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found or not permitted")
    if db_source.is_private != is_private:
        db_source.is_private = is_private
        await pgdb.commit()
        await pgdb.refresh(db_source)
    
    detail = SourceDetailResponse.model_validate(db_source)
    schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
    projection = {
            "tables": 0,
    }
    doc = await schema_collection.find_one({"_id": ObjectId(detail.doc_id)}, projection=projection)
    if doc:
        doc = copy_without_control_keys(doc)
        detail.source_name = doc.get("source_name","")
        detail.connection = doc.get("connection",{})
        detail.description = doc.get("description",[])
        detail.doc = doc
    return detail


@router.get("/{source_id}", response_model=SourceDetailResponse)
async def get_source(source_id: int, current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    result = await pgdb.execute(select(Source).filter( (Source.id == source_id) & ( (Source.user_id == current_user.id) | (Source.is_private == False) ) ))
    db_source = result.scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found or not permitted")
    detail = SourceDetailResponse.model_validate(db_source)
    schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
    projection = {
            "tables": 0,
    }
    doc = await schema_collection.find_one({"_id": ObjectId(detail.doc_id)}, projection=projection)
    if doc:
        doc = copy_without_control_keys(doc)
        detail.source_name = doc.get("source_name","")
        detail.connection = doc.get("connection",{})
        detail.description = doc.get("description",[])
        detail.doc = doc
    return detail


@router.delete("/{source_id}")
async def delete_source(source_id: int, current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    result = await pgdb.execute(select(Source).filter( (Source.id == source_id) & ( (Source.user_id == current_user.id) | (Source.is_private == False) ) ))
    db_source = result.scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found or not permitted")
    await pgdb.delete(db_source)
    await pgdb.commit()
    schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
    await schema_collection.delete_one({"_id": ObjectId(db_source.doc_id)})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("_types", response_model=List[SourceTypeResponse])
async def get_source_types(current_user: User = Depends(get_current_user), source_type_context = Depends(get_source_type_context)):
    supported_source_types = await st_mgr.get_supported_source_types(source_type_context)
    return [SourceTypeResponse(**source_type) for source_type in supported_source_types]


@router.get("_types/{source_type}", response_model=SourceTypeResponse)
async def get_source_types(source_type:str, current_user: User = Depends(get_current_user), source_type_context = Depends(get_source_type_context)):
    source_type_info = await st_mgr.get_source_type(source_type_context, source_type)
    return SourceTypeResponse(**source_type_info)


@router.post("/{source_type}/test_connectivity", response_model=SuccessOrErrorResponse)
async def test_connectivity(source_type:str, connection_info: dict = Body(...), current_user: User = Depends(get_current_user), source_type_context = Depends(get_source_type_context)):
    """
    {
        "host": "106.14.16.137",
        "port": 1444,
        "database" : "AdventureWorks2016_EXT",
        "username" : "sa",
        "password" : "Hong1234"
    }
    """
    if await st_mgr.test_connectivity(source_type_context, source_type, connection_info):
        return SuccessOrErrorResponse.model_validate({"success": True})
    else:
        return SuccessOrErrorResponse.model_validate({"success": False, "error": "failed to connect to source" })



@router.post("/{source_type}/entities", response_model=SuccessOrErrorResponse)
async def list_entities(source_type: str, connection_info: dict = Body(...), current_user: User = Depends(get_current_user), source_type_context = Depends(get_source_type_context)):
    entities = await st_mgr.list_entities(source_type_context, source_type, connection_info)
    if not entities:
        entities = []
    for entity in entities:
        entity["_selected"] = False  # 是否被选择，默认未被选择
    return SuccessOrErrorResponse.model_validate({"success": True, "data": entities})


@router.get("/entities/{source_id}", response_model=SuccessOrErrorResponse)
async def list_entities(source_id: int, current_user: User = Depends(get_current_user), source_type_context = Depends(get_source_type_context), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    # Both admin and regular user can access this endipoint
    conditions =  (Source.id == source_id)
    if current_user.role != "admin":
        # regular user only can get their own sources or public sources
        conditions = conditions & ( (Source.user_id == current_user.id) | (Source.is_private == False) )
    result = await pgdb.execute(select(Source).filter( conditions ))
    db_source = result.scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found or not permitted")
    source_type = db_source.source_type
    schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
    projection = {
        "_id": 0,
        "source_name": 1,
        "connection": 1,
        "tables": 1,
    }
    doc = await schema_collection.find_one({"_id": ObjectId(db_source.doc_id)}, projection=projection)
    if not doc:
        raise HTTPException(status_code=404, detail="Failed to fetch source document")
    connection_info = doc['connection']  # get source's connection info
    existing_tables = copy_without_control_keys(doc['tables'])
    existing_table_names = []
    for entity in existing_tables:
        entity['_selected'] = True  # All selected for exsisting tables
        existing_table_names.append(entity['table_name'])
    existing = {"tables": existing_tables}
    entities = await st_mgr.list_entities(source_type_context, source_type, connection_info)
    if not entities:
        entities = []
    for entity in entities:
        entity["_selected"] = False  # 是否被选择，默认未被选择
        if entity['table_name'] in existing_table_names:  # 如果之前有这个表，则被选择
            entity['_selected'] = True
    modified = {"tables": entities}
    options = {
        "primary_keys" : ["table_name", "column_name", "foreign_key_name", "lang"],  # There are the primary key to identify the schema info
        "allowed_update_keys" : ["description", "lang", "text", "domains", "tags" ], # The keys that can be updated
        "allowed_delete_keys" : ["tables", "columns"],  # The keys for allow removal
    }
    apply_changes(existing, modified, options, source_type_context.get_logger())  # apply database entities changes into existing schema data
    return SuccessOrErrorResponse.model_validate({"success": True, "data": existing})



@router.post("/{source_type}/create", response_model=SourceDetailResponse)
async def create_source(source_type: str, source_create : SourceCreateUpdate, current_user: User = Depends(get_current_user), source_type_context = Depends(get_source_type_context), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    db_source = await st_mgr.create_source(source_type_context, source_type, current_user, source_create.source_name, source_create.is_private, source_create.description, source_create.connection_info, source_create.additional_details, source_create.entities)
    detail = SourceDetailResponse.model_validate(db_source)
    schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
    projection = {
            "tables": 0,
    }
    doc = await schema_collection.find_one({"_id": ObjectId(detail.doc_id)}, projection=projection)
    if doc:
        doc = copy_without_control_keys(doc)
        detail.source_name = doc["source_name"]
        detail.connection = doc["connection"]
        detail.doc = doc
    return detail


@router.put("/update/{source_id}", response_model=SourceDetailResponse)
async def update_source(source_id: int, source_update : SourceCreateUpdate, current_user: User = Depends(get_current_user), source_type_context = Depends(get_source_type_context), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    # Both admin and regular user can access this endipoint
    conditions =  (Source.id == source_id)
    if current_user.role != "admin":
        # regular user only can get their own sources or public sources
        conditions = conditions & ( (Source.user_id == current_user.id) | (Source.is_private == False) )
    result = await pgdb.execute(select(Source).filter( conditions ))
    db_source = result.scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found or not permitted")
    source_type = db_source.source_type
    db_source = await st_mgr.update_source(source_type_context, source_type, current_user, source_id, source_update.source_name, source_update.is_private, source_update.description, source_update.connection_info, source_update.additional_details, source_update.entities)
    detail = SourceDetailResponse.model_validate(db_source)
    schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
    projection = {
            "tables": 0,
    }
    doc = await schema_collection.find_one({"_id": ObjectId(detail.doc_id)}, projection=projection)
    if doc:
        doc = copy_without_control_keys(doc)
        detail.source_name = doc["source_name"]
        detail.connection = doc["connection"]
        detail.doc = doc
    return detail



@router.post("/detect_relationships/{source_id}", response_model=SuccessOrErrorResponse)
async def detect_relationships(source_id : int, approach: DetectApproach = DetectApproach.NAME_BASED, current_user: User = Depends(get_current_user),  source_type_context = Depends(get_source_type_context), pgdb: AsyncSession = Depends(get_pgdb)):
    # Both admin and regular user can access this endipoint
    conditions =  (Source.id == source_id)
    if current_user.role != "admin":
        # regular user only can get their own sources or public sources
        conditions = conditions & ( (Source.user_id == current_user.id) | (Source.is_private == False) )
    result = await pgdb.execute(select(Source).filter( conditions ))
    db_source = result.scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found or not permitted")
    source_type = db_source.source_type
    task = await st_mgr.detect_relationships(source_type_context, source_type, source_id, approach)
    return SuccessOrErrorResponse.model_validate({"success": True, "data": task.id})


# @router.post("/embedding/{source_id}", response_model=SuccessOrErrorResponse)
# async def embedding(source_id : int, current_user: User = Depends(get_current_user),  source_type_context = Depends(get_source_type_context), pgdb: AsyncSession = Depends(get_pgdb)):
#     # Both admin and regular user can access this endipoint
#     conditions =  (Source.id == source_id)
#     if current_user.role != "admin":
#         # regular user only can get their own sources or public sources
#         conditions = conditions & ( (Source.user_id == current_user.id) | (Source.is_private == False) )
#     result = await pgdb.execute(select(Source).filter( conditions ))
#     db_source = result.scalar_one_or_none()
#     if not db_source:
#         raise HTTPException(status_code=404, detail="Source not found or not permitted")
#     source_type = db_source.source_type
#     task = await st_mgr.embedding(source_type_context, source_type, source_id)
#     return SuccessOrErrorResponse.model_validate({"success": True, "data": task.id})



@router.post("/table_annotate", response_model=SourceAnnotationResponse)
async def table_annotate(target: SourceAnnotationRequest, current_user: User = Depends(get_current_user)):
    target_json = target.model_dump()
    inputs = {
                "lang": ','.join(target.lang),
                "database_name": target.source_name,
                "database_description": ','.join([d.text for d in target.source_description]),
                "table_name": target.entity.table_name,
                "table_domains": ",".join(target.entity.domains),
                "columns": json.dumps(target_json['entity']['columns']),
                "primary_keys": ",".join(target.entity.primary_keys),
                "foreign_keys": json.dumps(target_json['entity']['foreign_keys']),
    }
    res = dify.call_dify(config.DIFY_WORKFLOW_ENDPOINT, config.DIFY_TABLE_ANNOTATION_APP_KEY, inputs = inputs)
    annotation = {}
    if res['data']['status'] == 'succeeded':
        answer = res['data']['outputs']['description']
        annotation = get_json(answer)
        return SourceAnnotationResponse.model_validate(annotation)
    else:
        error_message = f"dify api error {res['data']['error']}"
        raise Exception(error_message)


@router.post("/preview_data/{source_id}", response_model=SuccessOrErrorResponse)
async def preview_data(source_id: int, entity_name: str, current_user: User = Depends(get_current_user), source_type_context = Depends(get_source_type_context), pgdb: AsyncSession = Depends(get_pgdb)):
    # Both admin and regular user can access this endipoint
    conditions =  (Source.id == source_id)
    if current_user.role != "admin":
        # regular user only can get their own sources or public sources
        conditions = conditions & ( (Source.user_id == current_user.id) | (Source.is_private == False) )
    result = await pgdb.execute(select(Source).filter( conditions ))
    db_source = result.scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found or not permitted")
    source_type = db_source.source_type
    result = await st_mgr.preview_data(source_type_context, source_type, source_id, entity_name)
    return SuccessOrErrorResponse(success=True, data=result)

    
    

"""
txt	    text/plain
csv	    text/csv
json	application/json
pdf	    application/pdf
docx	application/vnd.openxmlformats-officedocument.wordprocessingml.document
xlsx	application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
zip	    application/zip
"""

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), media_type: str = Form(default=None),  current_user: User = Depends(get_current_user)):
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")
        file_data = await file.read()
        if not file_data:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Check file extension (must be .csv or .xlsx)
        base_name, ext = os.path.splitext(file.filename)
        if ext and ext.strip().lower() not in [".csv", ".xlsx"]:
            raise HTTPException(status_code=401, detail="Only CSV and XLSX are allowed.")

        file_obj = io.BytesIO(file_data)
        result = upload_fileobj("sources", file.filename, file_obj, current_user, file.content_type)
        return result
    except EndpointConnectionError:
        raise HTTPException(status_code=503, detail="S3 service is unavailable. Check the endpoint.")
    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="S3 authentication failed. Invalid credentials.")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 Client Error: {e.response['Error']['Message']}")
    except BotoCoreError as e:
        raise HTTPException(status_code=500, detail=f"Boto3 error: {str(e)}")
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during upload: {str(e)}")
    

@router.post("/download")
async def download_file(object_name: str = Form(...), default_media_type: str = Form(default="application/octet-stream"), current_user: User = Depends(get_current_user)):
    try:
        result = download_fileobj(object_name, default_media_type)
        file_obj = result["file_obj"]
        media_type = result["media_type"]
        filename_safe = result["filename_safe"]
        return Response(content=file_obj.getvalue(), media_type = media_type,
                         headers={"Content-Disposition": f"attachment; filename={filename_safe}"})
    except EndpointConnectionError:
        raise HTTPException(status_code=503, detail="S3 service is unavailable. Check the endpoint.")
    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="S3 authentication failed. Invalid credentials.")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 Client Error: {e.response['Error']['Message']}")
    except BotoCoreError as e:
        raise HTTPException(status_code=500, detail=f"Boto3 error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during download: {str(e)}")

