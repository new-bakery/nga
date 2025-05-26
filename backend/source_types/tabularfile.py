from util.module_discover import discover_modules, ModuleRegistry, ModuleContext
from sqlalchemy import create_engine
from sqlalchemy.sql import text as sql_text
from sqlalchemy.engine import Engine
from sqlalchemy.future import select
import urllib.parse
from bson import ObjectId
from celery import Celery, shared_task, current_app, chain
from celery.exceptions import MaxRetriesExceededError
import time
import asyncio
import pandas as pd
import base64
from uuid import UUID
from itertools import groupby
import networkx as nx
from networkx.readwrite import json_graph
import struct
import redis
from redis.commands.search.field import TagField, TextField, VectorField, NumericField
import json
import pandas as pd

from . import *
from dify import call_dify
from celery_app import worker
from models.user import User
from models.source import Source
from database import get_pgdb, get_mgdb
from source_types._relationships import DetectApproach, encode_minhash, minhash_signature, calculate_relationships
from config import config
from util.json_encoder import copy_without_control_keys
from util.tokenizer import get_token_count
from schemas.source import *
from ._shared import update_source_status
from ._detect_relationships import task_detect_relationships
from ._embedding import embedding, task_embedding 
from ._statistics import run_statistics, task_statistics, statistics
import s3_api


logger = logging.getLogger()

def on_init(context: ModuleContext, **kwargs):
    context.get_logger().info('initializing tabular file source type')


async def display_info() -> dict:
    return {
        "display_name"  : "Tabular File",
        "icon"          : "tabular-file.svg",
        "description"   : "Excel or CSV files containing tabular data (without specific formats or layouts, with column headers, starting from cell A1)",
    }
    

async def connection_info() -> dict:
    return {
        "Tabular Files" :dict(required=True, title="Tabular Files", hint="Select tabular files", allowed_exts = [".xlsx", ".csv"], multiple = True, file_uploader=True),
    }
    
async def build_connection_string(input_config: dict) -> str:
    return "excel+pandas"  # this is a historical magic word. check SQL Agent in dify "Get Query Schema Result" code block


async def test_connectivity(connection_info: dict) -> bool:
    # connection info should be dict like : {"file_objects": [{ "object_name" = "", "media_type" = "", "original_filename" = "" }] }
    fobjects = connection_info.get('file_objects', [])
    try:
        for info in fobjects:
            orinial_filename = info["original_filename"]
            downloaded = s3_api.download_fileobj(info["object_name"], info["media_type"])
            file_obj = downloaded["file_obj"]
            media_type = downloaded["media_type"]
            filename_safe = downloaded["filename_safe"].lower()  
            if filename_safe.endswith(".csv"):
                df = pd.read_csv(file_obj)
                if df.empty:
                    raise Exception(f"Empty CSV file : {orinial_filename}")
            elif filename_safe.endswith(".xlsx"):
                sheets = pd.read_excel(file_obj, sheet_name = None, engine='openpyxl')
                if all([df.empty for df in sheets.values()]):
                    raise Exception(f"Empty Excel file : {orinial_filename}")
        return True
    except Exception as e:
        raise


async def list_entities(connection_info: dict) -> list[dict]:
    try:
        # connection info should be dict like : {"file_objects": [{ "object_name" = "", "media_type" = "", "original_filename" = "" }] }
        fobjects = connection_info.get('file_objects', [])
        schemas = []
        tables = {}
        original_table_names = []
        table_name_mapping = {}
        for info in fobjects:
            orinial_filename = info["original_filename"]
            object_name = info["object_name"]
            media_type = info["media_type"]
            downloaded = s3_api.download_fileobj(object_name, info["media_type"])
            file_obj = downloaded["file_obj"]
            media_type = downloaded["media_type"]
            filename_safe = downloaded["filename_safe"].lower()  
            if filename_safe.endswith(".csv"):
                df = pd.read_csv(file_obj)
                table_name = filename_safe
                table_name_n = table_name
                n = original_table_names.count(table_name)
                if n > 0:
                    table_name_n = f"{table_name}_{n}"
                original_table_names.append(table_name)
                tables[table_name_n] = df
                table_name_mapping[table_name_n] = ('csv', orinial_filename, object_name, table_name, media_type)
            elif filename_safe.endswith(".xlsx"):
                sheets = pd.read_excel(file_obj, sheet_name=None, engine='openpyxl')
                for sheet_name, sheet_df in sheets.items():
                    table_name = sheet_name
                    table_name_n = table_name
                    n = original_table_names.count(table_name)
                    if n > 0:
                        table_name_n = f"{table_name}_{n}"
                    original_table_names.append(table_name)
                    tables[table_name_n] = sheet_df
                    table_name_mapping[table_name_n] = ('xlsx', orinial_filename, object_name, table_name, media_type)
                    
        for table_name, df in tables.items():
            df = df.convert_dtypes() # try to detect data types
            package = {
                    "table_name": table_name,
                    "file_type": table_name_mapping[table_name][0],
                    "original_file": table_name_mapping[table_name][1],
                    "object_name": table_name_mapping[table_name][2],
                    "sheet_name": table_name_mapping[table_name][3],
                    "media_type": table_name_mapping[table_name][4],
                    "description" : [],
                    "domains" : [],
                    "tags" : "",
                    "shape": [0, 0],
                    "columns": []
            }
            if not df.empty:
                package.update({
                    "shape": list(df.shape), # Need to change to list, since no tuple type in json. Tuple will cause jsondiff issue.
                    "columns": [{"column_name": col, 
                                "type": str(df[col].dtype), 
                                "description": [], 
                                "tags" : "",
                                "_signature": encode_minhash(minhash_signature(df[col].values.tolist())) } # Excel, always have signature !
                            for col in df.columns]
                })
            schemas.append(package)
        relationships = calculate_relationships(schemas, DetectApproach.NAME_AND_SIGNATURE_BASED, config.SIGNATURE_THRESHOLD, config.NAME_TYPE_THRESHOLD)
        relationships.sort(key=lambda x: x["primary_table"])
        # TODO: we need check if the foreign key data are set to primary table ? Or should be foreign table ?
        grouped_relationships = {k: list(v) for k, v in groupby(relationships, key=lambda x: x["primary_table"])}
        for table_schema in schemas:
            if "primary_keys" not in table_schema:
                table_schema["primary_keys"] = []
            if "foreign_keys" not in table_schema:
                table_schema["foreign_keys"] = []
            table_schema["foreign_keys"].extend(grouped_relationships.get(table_schema["table_name"], []))
        return schemas
    except Exception as e:
        logger.error(f"Error extracting schema: {str(e)}")
        raise
    

async def create_source(current_user: User, name: str, is_private : bool, description: list[LangDescriptionModel], connection_info: dict, additional_details: str, entities: list[EntitySchemaModel]) :

    # TODO: Need to validate "file_type", "original_file", "object_name" , "sheet_name", "media_type"
    for entity in entities:
        file_type = entity.file_type
        original_file = entity.original_file
        object_name = entity.object_name
        sheet_name = entity.sheet_name
        media_type = entity.media_type
        
        if file_type not in ['csv', 'xls', 'xlsx']: # remove xls later
            raise Exception(f"Invalid file type {file_type}")
        
        if len(str.strip(object_name)) == 0:
            raise Exception("Invalid object name")
        
        if file_type in ['xls', 'xlsx']: # remvoe xls later
            if len(str.strip(sheet_name)) == 0:
                raise Exception("Invalid sheet_name")
            
        if not s3_api.check_exists(object_name):
            raise Exception(f"{object_name} not found")

    if entities:
        included_table_names = {entity.table_name for entity in entities}
        for entity in entities:
            foreign_keys = entity.foreign_keys
            if foreign_keys:
                # 过滤外键，去掉不符合条件的外键
                entity.foreign_keys = [
                    fkey for fkey in foreign_keys 
                    if fkey.primary_table in included_table_names and fkey.foreign_table in included_table_names
                ]
                
    doc = {
            "source_name" : name,
            "description" : [LangDescriptionModel.model_dump(d) for d in description] ,
            "tables" : [EntitySchemaModel.model_dump(e) for e in entities],
            "additional_details" : additional_details,
            "connection" : connection_info,
            "connection_string" : await build_connection_string(connection_info),
            "dialect" : "duckdb_engine",
            "driver" : "duckdb",
    }
    
    
    
    doc_id = None
    async for mgdb in get_mgdb():
        schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
        result = await schema_collection.insert_one(doc)
        doc_id = result.inserted_id
    
    source_data = {"source_type": "tabularfile", "is_private": is_private, "user_id": current_user.id, "doc_id": str(doc_id), "status" : {}}
    db_source = Source(**source_data)
    async for pgdb in get_pgdb():
        pgdb.add(db_source)
        await pgdb.commit()
        await pgdb.refresh(db_source)
    
    await statistics(db_source.id)
    await embedding(db_source.id)
    
    return db_source



async def update_source(current_user: User, source_id: int, name: str, is_private : bool, description: list[LangDescriptionModel], connection_info: dict, additional_details: str, entities: list[EntitySchemaModel]) :
    
    # TODO: Need to validate "file_type", "original_file", "object_name" , "sheet_name", "media_type"
    for entity in entities:
        file_type = entity.file_type
        original_file = entity.original_file
        object_name = entity.object_name
        sheet_name = entity.sheet_name
        media_type = entity.media_type
        
        if file_type not in ['csv', 'xls', 'xlsx']: # remove xls later
            raise Exception(f"Invalid file type {file_type}")
        
        if len(str.strip(object_name)) == 0:
            raise Exception("Invalid object name")
        
        if file_type in ['xls', 'xlsx']: # remvoe xls later
            if len(str.strip(sheet_name)) == 0:
                raise Exception("Invalid sheet_name")
            
        if not s3_api.check_exists(object_name):
            raise Exception(f"{object_name} not found")
        
    
    async for pgdb in get_pgdb():
        result = await pgdb.execute(select(Source).filter( (Source.id == source_id) ))
        db_source = result.scalar_one_or_none()
        if not db_source:
            raise Exception("Source not found")
        if db_source.source_type != "tabularfile":
            raise Exception("Source type not supported")

        doc_id = db_source.doc_id
        
        if entities:
            included_table_names = {entity.table_name for entity in entities}
            for entity in entities:
                foreign_keys = entity.foreign_keys
                if foreign_keys:
                    # 过滤外键，去掉不符合条件的外键
                    entity.foreign_keys = [
                        fkey for fkey in foreign_keys 
                        if fkey.primary_table in included_table_names and fkey.foreign_table in included_table_names
                    ]
        doc = {
                "source_name" : name,
                "description" : [LangDescriptionModel.model_dump(d) for d in description] ,
                "tables" : [EntitySchemaModel.model_dump(e) for e in entities],
                "additional_details" : additional_details,
                "connection" : connection_info,
                "connection_string" : await build_connection_string(connection_info),
                "dialect" : "duckdb_engine",
                "driver" : "duckdb",
        }
        
        
        async for mgdb in get_mgdb(): 
            schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
            result = await schema_collection.update_one({"_id": ObjectId(doc_id)}, {"$set": doc})
            if result.matched_count == 0:
                raise Exception("Failed to update target document")
        
        db_source.is_private = is_private
    
        await pgdb.commit()
        await pgdb.refresh(db_source)
    
    await statistics(db_source.id)
    await embedding(db_source.id)
    
    return db_source
    

async def detect_relationships(source_id : int, approach: DetectApproach):
    approach = DetectApproach.NAME_AND_SIGNATURE_BASED  # FIXED
    task1 = task_calculate_signature.s(source_id, approach.value) 
    task2 = task_detect_relationships.s(source_id, approach.value)
    result = chain(task1, task2).apply_async()
    return result


@shared_task(bind=True)
def task_calculate_signature(self, source_id : int, approach: str):
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(run_calculate_signature(source_id, approach))
    except Exception as ex:
        logger.error(ex)
        raise
    

async def run_calculate_signature(source_id : int, approach: str):
    try:
        approach = DetectApproach(approach)
        logger.info(f'calculating relationships with by approach {approach.value}')
        db_source = await update_source_status(source_id, {"calculate_signatures": "running"})
        doc_id = db_source.doc_id
        if not doc_id:
            raise Exception("Failed to fetch source data")
        async for mgdb in get_mgdb():
            schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
            doc = await schema_collection.find_one({"_id": ObjectId(doc_id)})
        if not doc:
            raise Exception("Failed to fetch source doc")
        connection_info = doc.get('connection', {})
        table_schemas = doc.get('tables', [])
        await impl_calculate_signatures(connection_info, table_schemas)
        doc = await schema_collection.update_one({"_id": ObjectId(doc_id)}, {'$set': doc})
        db_source = await update_source_status(source_id, {"calculate_signatures": "done"})
    except Exception as ex:
        db_source = await update_source_status(source_id, {"calculate_signatures": "failed", "error": str(ex)})
        
        

async def impl_calculate_signatures(connection_info, table_schemas):
    # Calculate Signature, SHAPE
    
    cache = {}
    
    for schema in table_schemas:
        table_name = schema["table_name"]
        file_type = schema["file_type"]
        original_file = schema["original_file"]
        object_name = schema["object_name"]
        sheet_name = schema["sheet_name"]
        media_type = schema["media_type"]

        if object_name not in cache:
            downloaded = s3_api.download_fileobj(object_name, media_type)
            cache[object_name] = downloaded
        else:
            downloaded = cache[object_name]

        file_obj = downloaded["file_obj"]
        file_obj.seek(0)  # reset the file pointer to the beginning
        media_type = downloaded["media_type"]
        filename_safe = downloaded["filename_safe"].lower()  

        if file_type == 'csv':
            df = pd.read_csv(file_obj)
        elif file_type in ['xls', 'xlsx']: # remvoe xls later
            df = pd.read_excel(file_obj, sheet_name=sheet_name)

        for column in schema['columns']:
            column["_signature"] = encode_minhash(minhash_signature(df[column["column_name"]].values.tolist()))
        
    return table_schemas



async def preview_data(source_id: int, entity_name: dict, limit: int = 50):
    # The entity_name here will be :  json string:
    # {"original_file": "", "sheet_name": ""}
    
    entity_info = json.loads(entity_name)
    original_file = entity_info["original_file"]
    sheet_name = entity_info.get("sheet_name")
    
    async for pgdb in get_pgdb():
        result = await pgdb.execute(select(Source).filter( (Source.id == source_id) ))
        db_source = result.scalar_one_or_none()
        if not db_source:
            raise Exception("Source not found")
        doc_id = db_source.doc_id
        if not doc_id:
            raise Exception("Failed to fetch source data")
        async for mgdb in get_mgdb():
            schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
            doc = await schema_collection.find_one({"_id": ObjectId(doc_id), "tables.original_file": original_file, "tables.sheet_name": sheet_name}, {"tables.$": 1, "connection" : 1})
        if not doc:
            raise Exception("Failed to fetch source doc")
    table_schema = doc['tables'][0]
    table_name = table_schema["table_name"]
    file_type = table_schema["file_type"]
    original_file = table_schema["original_file"]
    object_name = table_schema["object_name"]
    sheet_name = table_schema["sheet_name"]
    media_type = table_schema["media_type"]
    
    downloaded = s3_api.download_fileobj(object_name, media_type)
    file_obj = downloaded["file_obj"]
    if file_type == 'csv':
            df = pd.read_csv(file_obj)
    elif file_type in ['xls', 'xlsx']: # remvoe xls later
        df = pd.read_excel(file_obj, sheet_name=sheet_name)
        
    df = df.head(limit)
    data = df.to_dict(orient='records')
    normalized_data = [
        {
            key.strip('"'): (
                str(value) if isinstance(value, UUID)  # 转换 UUID 为字符串
                else base64.b64encode(value).decode('utf-8') if isinstance(value, bytes)  # 转换 bytes 为 Base64
                else value.isoformat() if isinstance(value, pd.Timestamp)  # 转换 datetime 为 ISO 格式字符串
                else None if pd.isna(value)  # 将 NaN 或 None 转为 None（JSON 中的 null）
                # else str(value) if isinstance(value, bool)  # 转换布尔值为字符串
                # else None if isinstance(value, float) and (value == float('inf') or value == float('-inf'))  # 处理 inf
                # else str(value) if isinstance(value, str) and value == ""  # 空字符串转为 None
                # else str(value) if isinstance(value, int) and abs(value) > 2**53 - 1  # 处理大整数
                else value  # 保留其他类型
            )
            for key, value in row.items()
        }
        for row in data
    ]
    return normalized_data

