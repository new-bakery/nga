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

from . import *
from dify import call_dify
from celery_app import worker
from models.user import User
from models.source import Source
from database import get_pgdb, get_mgdb
from source_types._relationships import DetectApproach, encode_minhash, minhash_signature
from config import config
from util.json_encoder import copy_without_control_keys
from util.tokenizer import get_token_count
from schemas.source import *
from ._shared import update_source_status
from ._detect_relationships import task_detect_relationships, build_graph
from ._embedding import embedding, task_embedding
from ._statistics import run_statistics, task_statistics, statistics


logger = logging.getLogger()

def on_init(context: ModuleContext, **kwargs):
    context.get_logger().info('initializing sqlserver source type')
    # current_app.tasks.register(task_detect_relationships)
    # current_app.tasks.register(task_embedding)
    # current_app.tasks.register(task_statistics)

async def display_info() -> dict:
    return {
        "display_name"  : "Microsoft SQL Server",
        "icon"          : "microsoft-sql-server.svg",
        "description"   : "Microsoft SQL Server Database as Source",
    }

async def connection_info() -> dict:
    return {
        "host": dict(required=True, title="Host", hint="Your SQL Server host or IP address", quote=True, default=None),
        "port": dict(required=False, title="Port", hint="SQL Server default port", quote=False, default="1433"),
        "database": dict(required=True, title="Database", hint="Target database name", quote=True, default=None),
        "username": dict(required=True, title="User Name", hint="Database username", quote=True, default=None),
        "password": dict(required=True, title="Password", hint="Database password", quote=True, default=None, secret=True),
        # "driver": dict(rquired=False, title="Driver", hint="e.g. SQL Server, ODBC Driver 17 for SQL Server", quote=True, default="ODBC Driver 18 for SQL Server"),
        # "trusted_connection": dict(required=False, title="Trusted Connection", hint="Use Windows Authentication (yes or no)", quote=False, default=None, allowed=["yes", "no"]),  # This is PyODBC
        "encrypt": dict(required=False, title="Encrypt", hint="Enable encrypted connection (yes or no)", quote=False, default=None, allowed=["yes", "no"]),
        "timeout": dict(required=False, title="Time Out", hint="Connection timeout in seconds", quote=False, default=None),
        "application_name": dict(required=False, title="Application Name", hint="Application name for tracking", quote=True, default=None),
        "instance": dict(required=False, title="Instance", hint="SQL Server named instance (e.g. SQLEXPRESS)", quote=True, default=None),
        "autocommit": dict(required=False, title="Auto Commit", hint="Enable auto-commit transactions (True or False)", quote=False, default=None, allowed=["true", "false"]),
        "ssl": dict(required=False, title="SSL", hint="Enable SSL connection (yes or no)", quote=False, default=None, allowed=["yes", "no"]),
        "charset": dict(required=False, title="Charset", hint="e.g. UTF-8", quote=False, default=None),
        # "TrustServerCertificate": dict(required=False, title="Trust Server Certificate", hint="Whether trust SQL Server Certificate", quote=False, default=config.TRUSTSERVERCERTIFICATE, allowed=["yes", "no"]),
  
    }
    
async def detect_relationships(source_id : int, approach: DetectApproach):
    if approach in [DetectApproach.SIGNATURE_BASED, DetectApproach.NAME_AND_SIGNATURE_BASED]:
        task1 = task_calculate_signature.s(source_id, approach.value) 
        task2 = task_detect_relationships.s(source_id, approach.value)
        result = chain(task1, task2).apply_async()
    else:
        # task = task_detect_relationships.apply_async((source_id, approach.value))  # 启动 Celery 任务
        result = task_detect_relationships.delay(None, source_id, approach.value)
    logger.info(f'celery task detect_relationships started')
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
    connection_string = await build_connection_string(connection_info)
    engine: Engine = create_engine(connection_string, echo=config.DB_ECHO)
    with engine.connect() as connection:
        for table_schema in table_schemas:
            logger.info(f'calcuating signature for {table_schema['table_name']}')
            # If a table already got all signatures, pass
            # if not all(["_signature" in column_schema for column_schema in table_schema["columns"]]): 
            # When this function called, means, recalculate all signatures
            if True:
                count = get_table_count(connection, table_schema)
                max_rows_to_signature = config.MAX_ROWS_TO_SIGNATURE
                to_limit = max_rows_to_signature if count > max_rows_to_signature else 0
                data = get_table_data(connection, table_schema, to_limit)
                if len(data) > 0:
                    normalized_data = [
                        {
                            key.strip('"'): (
                                str(value) if isinstance(value, UUID)  # Convert UUID to string
                                else base64.b64encode(value).decode('utf-8') if isinstance(value, bytes)  # Convert bytes to Base64
                                else value  # Keep other types as is
                            )
                            for key, value in row.items()
                        }
                        for row in data
                    ]
                    df = pd.DataFrame(normalized_data)
                    table_schema["shape"] = list(df.shape)
                    table_schema["shape"][0] = count # put the real count back in
                    for column_schema in table_schema["columns"]:
                        col = column_schema["column_name"]
                        column_schema["_signature"] = encode_minhash(minhash_signature(df[col].values.tolist()))
    return table_schemas


async def build_connection_string(input_config: dict) -> str:
    schema = await connection_info()  # 获取 schema 结构
    parts = {}
  
    for k, v in schema.items():
        value = None
        value = v["default"]
        if k in input_config:
            value = input_config[k]
        if v.get("required", False) and value is None:
            raise ValueError(f"Missing required field: {k}")
        if value is not None:
            if v.get("quote", False):
                value = urllib.parse.quote_plus(value)
            if 'allowed' in v and isinstance(v['allowed'], list):
                if value not in v['allowed']:
                    raise ValueError(f"Invalid value for field {k}: {value}. Allowed values are {v['allowed']}")
        if value is not None:
            parts[k] = value
    
    username = parts.pop('username')
    password = parts.pop('password')
    host = parts.pop('host')
    port = parts.pop('port')
    database = parts.pop('database')
    
    # conn_str = f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}"  # 不打算使用pyodbc实现异步数据库连接（不成熟）
    conn_str = f"mssql+pymssql://{username}:{password}@{host}:{port}/{database}"  # ODBC居然由字段不认识

    query_params = []
    for key, value in parts.items():
        query_params.append(f"{key}={value}")

    if query_params:
        conn_str += "?" + "&".join(query_params)

    return conn_str

async def test_connectivity(connection_info: dict) -> bool:
    connection_string = await build_connection_string(connection_info)
    try:
        engine = create_engine(connection_string)
        engine.connect()
        return True
    except Exception as e:
        raise
    


# this will return tables and views
def get_tables(connection):
    sql = sql_text("""
        SELECT 
            t.TABLE_SCHEMA, 
            t.TABLE_NAME, 
            CAST(ep.value AS NVARCHAR(MAX)) AS DESCRIPTION
        FROM 
            INFORMATION_SCHEMA.TABLES t
        LEFT JOIN 
            sys.objects o
            ON t.TABLE_NAME = o.name
            AND o.type = 'U'
        LEFT JOIN 
            sys.extended_properties ep
            ON o.object_id = ep.major_id
            AND ep.minor_id = 0 
            AND ep.class = 1 
            AND ep.name = 'MS_Description'
        WHERE 
            t.TABLE_TYPE = 'BASE TABLE'
    """)

    cur = connection.execute(sql)
    tables = cur.fetchall()
    return tables

def get_columns(connection):
    sql = sql_text("""
        SELECT 
            COLUMNS.TABLE_SCHEMA, 
            COLUMNS.TABLE_NAME, 
            COLUMNS.COLUMN_NAME, 
            COLUMNS.DATA_TYPE, 
            COLUMNS.IS_NULLABLE, 
            CAST(ep.value AS NVARCHAR(MAX)) AS DESCRIPTION
        FROM 
            INFORMATION_SCHEMA.COLUMNS
        INNER JOIN 
            INFORMATION_SCHEMA.TABLES 
            ON 
                COLUMNS.TABLE_CATALOG = TABLES.TABLE_CATALOG
                AND COLUMNS.TABLE_SCHEMA = TABLES.TABLE_SCHEMA
                AND COLUMNS.TABLE_NAME = TABLES.TABLE_NAME
        LEFT JOIN 
            sys.objects o
            ON TABLES.TABLE_NAME = o.name
            AND o.type = 'U'
        LEFT JOIN 
            sys.columns sc
            ON o.object_id = sc.object_id
            AND COLUMNS.COLUMN_NAME = sc.name
        LEFT JOIN 
            sys.extended_properties ep
            ON sc.object_id = ep.major_id
            AND sc.column_id = ep.minor_id
            AND ep.class = 1
            AND ep.name = 'MS_Description'
        ORDER BY
            COLUMNS.TABLE_SCHEMA,
            COLUMNS.TABLE_NAME,
            COLUMNS.ORDINAL_POSITION
    """)

    cur = connection.execute(sql)
    columns = cur.fetchall()
    return columns


def get_primary_keys(connection):
    sql = sql_text("""
        SELECT 
            KCU.TABLE_SCHEMA, 
            KCU.TABLE_NAME, 
            KCU.COLUMN_NAME
        FROM 
            INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS TC 
				INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU 
					ON 
						TC.CONSTRAINT_TYPE = 'PRIMARY KEY'
					AND TC.CONSTRAINT_CATALOG = KCU.CONSTRAINT_CATALOG
					AND TC.CONSTRAINT_SCHEMA = KCU.CONSTRAINT_SCHEMA
					AND TC.CONSTRAINT_NAME = KCU.CONSTRAINT_NAME
					AND TC.TABLE_CATALOG = KCU.TABLE_CATALOG
					AND TC.TABLE_SCHEMA = KCU.TABLE_SCHEMA
					AND TC.TABLE_NAME = KCU.TABLE_NAME
                   
				INNER JOIN INFORMATION_SCHEMA.TABLES AS T
					ON
						T.TABLE_CATALOG = TC.TABLE_CATALOG
					AND T.TABLE_SCHEMA = TC.TABLE_SCHEMA
					AND T.TABLE_NAME = TC.TABLE_NAME
    """)
    cur = connection.execute(sql)
    primary_keys = cur.fetchall()
    return primary_keys


def get_foreign_keys(connection):
    sql = sql_text("""
                SELECT 
                    TFK.TABLE_SCHEMA AS FK_TABLE_SCHEMA,
                    TFK.TABLE_NAME AS FK_TABLE_NAME,
                    KCUFK.COLUMN_NAME AS FK_COLUMN_NAME,
                    TPK.TABLE_SCHEMA AS PK_TABLE_SCHEMA,
                    TPK.TABLE_NAME AS PK_TABLE_NAME,
                    KCUPK.COLUMN_NAME AS PK_COLUMN_NAME
                FROM 
                    INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS AS RC
                            INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS TCFK 
                                ON 
                                        RC.CONSTRAINT_CATALOG = TCFK.CONSTRAINT_CATALOG
                                    AND RC.CONSTRAINT_SCHEMA = TCFK.CONSTRAINT_SCHEMA
                                    AND RC.CONSTRAINT_NAME = TCFK.CONSTRAINT_NAME
                                    AND TCFK.CONSTRAINT_TYPE = 'FOREIGN KEY'

                            INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS TCPK 
                                ON 
                                            RC.UNIQUE_CONSTRAINT_CATALOG = TCPK.CONSTRAINT_CATALOG
                                        AND RC.UNIQUE_CONSTRAINT_SCHEMA = TCPK.CONSTRAINT_SCHEMA
                                        AND	RC.UNIQUE_CONSTRAINT_NAME = TCPK.CONSTRAINT_NAME
                                        AND TCPK.CONSTRAINT_TYPE = 'PRIMARY KEY'
                            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCUFK

                                ON 
                                            TCFK.CONSTRAINT_CATALOG = KCUFK.CONSTRAINT_CATALOG
                                        AND	TCFK.CONSTRAINT_SCHEMA = KCUFK.CONSTRAINT_SCHEMA
                                        AND TCFK.CONSTRAINT_NAME = KCUFK.CONSTRAINT_NAME

                            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCUPK
                                ON 
                                            TCFK.CONSTRAINT_CATALOG = KCUPK.CONSTRAINT_CATALOG
                                        AND	TCFK.CONSTRAINT_SCHEMA = KCUPK.CONSTRAINT_SCHEMA
                                        AND TCFK.CONSTRAINT_NAME = KCUPK.CONSTRAINT_NAME

                            INNER JOIN INFORMATION_SCHEMA.TABLES AS TPK
                                ON
                                            TPK.TABLE_CATALOG = TCPK.TABLE_CATALOG
                                        AND TPK.TABLE_SCHEMA = TCPK.TABLE_SCHEMA
                                        AND TPK.TABLE_NAME = TCPK.TABLE_NAME

                            INNER JOIN INFORMATION_SCHEMA.TABLES AS TFK
                                ON
                                            TFK.TABLE_CATALOG = TCFK.TABLE_CATALOG
                                        AND TFK.TABLE_SCHEMA = TCFK.TABLE_SCHEMA
                                        AND TFK.TABLE_NAME = TCFK.TABLE_NAME
    """)
    cur = connection.execute(sql)
    foreign_keys = cur.fetchall()
    return foreign_keys


async def list_entities(connection_info: dict) -> list[dict]:
    def _get_description(row, lang) -> list:
        description = []
        if row.DESCRIPTION and len(row.DESCRIPTION) > 0:
            description.append({"lang": lang, "text": row.DESCRIPTION})
        return description

    try:
        connection_string = await build_connection_string(connection_info)
        engine: Engine = create_engine(connection_string, echo=config.DB_ECHO)
        with engine.connect() as connection:
            tables = get_tables(connection)
            columns = get_columns(connection)
            primary_keys = get_primary_keys(connection)
            foreign_keys = get_foreign_keys(connection)
        schema = []
        lang = config.DB_LANG
        for table in tables:
            table_full_name = f'{table.TABLE_SCHEMA}.{table.TABLE_NAME}'
            package = {"table_name" : table_full_name, "description" : _get_description(table, lang), "domains" : [], "tags" : ""}
            package["columns"] = [{"column_name" : column.COLUMN_NAME, "type": column.DATA_TYPE, "description" : _get_description(column, lang)  , "tags" : ""}
                                    for column in columns if f'{column.TABLE_SCHEMA}.{column.TABLE_NAME}' == table_full_name]
            package["primary_keys"] = [pk.COLUMN_NAME for pk in primary_keys if f'{pk.TABLE_SCHEMA}.{pk.TABLE_NAME}' == table_full_name]
            # TODO: we need check if the foreign key data are set to primary table ? Or should be foreign table ?
            package["foreign_keys"] = [ {"foreign_key_name": f'{fk.PK_TABLE_SCHEMA}.{fk.PK_TABLE_NAME}.{fk.PK_COLUMN_NAME} <-> {fk.FK_TABLE_SCHEMA}.{fk.FK_TABLE_NAME}.{fk.FK_COLUMN_NAME}' , \
                                        "primary_table": f'{fk.PK_TABLE_SCHEMA}.{fk.PK_TABLE_NAME}' , \
                                        "primary_column" : fk.PK_COLUMN_NAME , \
                                        "foreign_table" : f'{fk.FK_TABLE_SCHEMA}.{fk.FK_TABLE_NAME}' , \
                                        "foreign_column" : fk.FK_COLUMN_NAME , \
                                        "by": "design" } 
                                        for fk in foreign_keys if f'{fk.PK_TABLE_SCHEMA}.{fk.PK_TABLE_NAME}' == table_full_name]
            schema.append(package)
        return schema
    except Exception as e:
        logger.error(f"Error extracting schema: {str(e)}")
        raise

async def create_source(current_user: User, name: str, is_private : bool, description: list[LangDescriptionModel], connection_info: dict, additional_details: str, entities: list[EntitySchemaModel]) :
    
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
            "dialect" : "mssql",
            "driver" : "pymssql",
    }
    
    await build_graph(doc)
    
    doc_id = None
    async for mgdb in get_mgdb():
        schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
        result = await schema_collection.insert_one(doc)
        doc_id = result.inserted_id
    
    source_data = {"source_type": "sqlserver", "is_private": is_private, "user_id": current_user.id, "doc_id": str(doc_id), "status" : {}}
    db_source = Source(**source_data)
    async for pgdb in get_pgdb():
        pgdb.add(db_source)
        await pgdb.commit()
        await pgdb.refresh(db_source)
    
    await statistics(db_source.id)
    await embedding(db_source.id)
    
    
    
    return db_source

    

async def update_source(current_user: User, source_id: int, name: str, is_private : bool, description: list[LangDescriptionModel], connection_info: dict, additional_details: str, entities: list[EntitySchemaModel]) :
    
    async for pgdb in get_pgdb():
        result = await pgdb.execute(select(Source).filter( (Source.id == source_id) ))
        db_source = result.scalar_one_or_none()
        if not db_source:
            raise Exception("Source not found")
        if db_source.source_type != "sqlserver":
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
                "dialect" : "mssql",
                "driver" : "pymssql",
        }
        
        await build_graph(doc)
        
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
    

def get_table_count(connection, table_schema: dict):
    sql = sql_text(f"""
        SELECT COUNT(*) AS row_count
        FROM {table_schema["table_name"]}
    """)
    cur = connection.execute(sql)
    row_count = cur.fetchall()
    return row_count[0].row_count


def get_table_data(connection, table_schema: dict, limit: int = 0):
    columns = [f"[{column_schema["column_name"]}]" for column_schema in table_schema["columns"]]
    sql = sql_text(f"""
        SELECT {'TOP ' + str(limit) if limit > 0 else ''}
        {', '.join(columns)}
        FROM {table_schema["table_name"]}
    """)
    cur = connection.execute(sql)
    data = cur.mappings().all() # 
    # data = cur.fetchall()
    return data



async def preview_data(source_id: int, entity_name: dict, limit: int = 50):
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
            doc = await schema_collection.find_one({"_id": ObjectId(doc_id), "tables.table_name": entity_name}, {"tables.$": 1, "connection" : 1})
        if not doc:
            raise Exception("Failed to fetch source doc")
        connection_info = doc['connection']
        table_schema = doc['tables'][0]
        connection_string = await build_connection_string(connection_info)
        engine: Engine = create_engine(connection_string, echo=config.DB_ECHO)
        with engine.connect() as connection:
            data = get_table_data(connection, table_schema, limit)
            if len(data) > 0:
                    normalized_data = [
                        {
                            key.strip('"'): (
                                str(value) if isinstance(value, UUID)  # Convert UUID to string
                                else base64.b64encode(value).decode('utf-8') if isinstance(value, bytes)  # Convert bytes to Base64
                                else value  # Keep other types as is
                            )
                            for key, value in row.items()
                        }
                        for row in data
                    ]
            return normalized_data
    

        
