import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pymongo
import duckdb
import argparse
from typing import List
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import uvicorn
import pandas as pd
import datetime
import time
import threading
import io
import logging
from logging.handlers import TimedRotatingFileHandler
from urllib.parse import unquote
import json
import traceback
from fastapi.responses import JSONResponse
from bson import ObjectId

from config import config
import s3_api

def setup_logger():
    logger = logging.getLogger("default_logger")
    logger.setLevel(logging.INFO)

    log_dir = "logs"
    log_file_path = os.path.join(log_dir, "pondsql.log")
    os.makedirs(log_dir, exist_ok=True)

    handler = TimedRotatingFileHandler(
        log_file_path, when="midnight", interval=1, backupCount=10, encoding="utf-8"
    )
    handler.suffix = "%Y-%m-%d"
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()



_global_schema_mongodb_connection_string = config.MONGODB_CONNECTION_STRING
_global_schema_mongodb_database = config.MONGODB_DATABASE_NAME
_global_schema_mongodb_collection = config.SCHEMA_COLLECTION_NAME
_global_pondsql_port = 8456
_global_database_timeout = 3600
_global_database_cache = {}
_cache_lock = threading.Lock()

load_dotenv()
app = FastAPI()

def unload_inactive_databases():
    global _global_database_cache
    while True:
        try:
            current_time = datetime.datetime.now()
            to_remove = []
            for source, (conn, last_access_time) in _global_database_cache.items():
                if (current_time - last_access_time).total_seconds() > _global_database_timeout:
                    logger.info(f"unloading database {source} due to timeout")
                    to_remove.append(source)
            for source in to_remove:
                with _cache_lock:
                    conn = _global_database_cache[source][0]
                    conn.close() 
                    del _global_database_cache[source]
                    logger.info(f"unloaded database {source} due to timeout")
            time.sleep(60*5) 
        except Exception as e:
            logger.error(f"Error in cleanup thread: {e}")

cleanup_thread = threading.Thread(target=unload_inactive_databases, daemon=True)
cleanup_thread.start()

def load_source(source_doc_id):
    global _global_database_cache
    logger.info(f"loading database {source_doc_id} to memory")

    client = pymongo.MongoClient(_global_schema_mongodb_connection_string)
    db = client[_global_schema_mongodb_database]
    collection = db[_global_schema_mongodb_collection]

    # database_schema = collection.find_one({DATABASE_NAME: source})
    database_schema = collection.find_one({"_id": ObjectId(source_doc_id)})  # Now we start to use source_doc_id
    if not database_schema:
        logger.error(f"database {source_doc_id} not found")
        raise Exception(f"database {database_schema} not found")
    
    connection_string = database_schema.get("connection_string", '')
    if not connection_string.startswith('excel+pandas'):
        logger.error(f"database {source_doc_id} is not a excel+pandas database")
        raise Exception(f"database {source_doc_id} is not a excel+pandas database")
    
    logger.info('creating duckdb connection')
    conn = duckdb.connect(":memory:")
    
    loaded_excel_file = {}
    for table_schema in database_schema["tables"]:
        table_name = table_schema["table_name"]
        file_type = table_schema["file_type"]
        original_file = table_schema["original_file"]
        object_name = table_schema["object_name"]
        sheet_name = table_schema["sheet_name"]
        media_type = table_schema["media_type"]
        
        logger.info(f"table_name = {table_name}")
        logger.info(f"file_type = {file_type}")
        logger.info(f"original_file = {original_file}")
        logger.info(f"object_name = {object_name}")
        logger.info(f"sheet_name = {sheet_name}")
        logger.info(f"media_type = {media_type}")

        if object_name not in loaded_excel_file:
            logger.info(f"downloading object : {object_name}")
            downloaded = s3_api.download_fileobj(object_name, media_type)
            loaded_excel_file[object_name] = downloaded
        else:
            logger.info(f"fetching cached object : {object_name}")
            downloaded = loaded_excel_file[object_name]
        
        file_obj = downloaded["file_obj"]
        file_obj.seek(0)
        
        logger.info('loading dataframes ...')
        filename_safe = downloaded["filename_safe"].lower()
        if filename_safe.endswith('.csv'):
            df = pd.read_csv(file_obj)
        elif filename_safe.endswith('.xlsx'):
            df = pd.read_excel(file_obj, sheet_name = sheet_name, engine='openpyxl')
        df = df.convert_dtypes() # try to detect data types
        logger.info(f'registering table {table_name} {df.shape}')
        conn.register(table_name, df)
    
    with _cache_lock:
        _global_database_cache[source_doc_id] = (conn, datetime.datetime.now())


# This is to ensure the error message is returned to the client (e.g. LLM, so that it can react to the error)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    stack_trace = traceback.format_exc()
    logger.error(f"An error occurred: {str(exc)}")
    logger.error(f"Stack trace: {stack_trace}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "message": str(exc),
            "stack_trace": stack_trace,
        }
    )

class QueryRequest(BaseModel):
    source_doc_id: str
    query: str

@app.post("/query/")
async def query(request: QueryRequest):
    global _global_database_cache
    if request.source_doc_id not in _global_database_cache:
        try:
            logger.info(f"loading {request.source_doc_id} since its not in memory")
            load_source(request.source_doc_id)
        except Exception as e:
            logger.error(f"Error loading {request.source_doc_id}: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=404, detail="Database not found or failed to load")
    try:
        logger.info('updating latest access time')
        conn = _global_database_cache[request.source_doc_id][0]
        _global_database_cache[request.source_doc_id] = (conn, datetime.datetime.now())
        logger.info(f'executing query {request.query}')
        result = conn.execute(request.query).fetchall()
        columns = [desc[0] for desc in conn.description]
        result = [dict(zip(columns, row)) for row in result]
        logger.info(f'returning result of {len(result)} rows')
        return result
    except Exception as e:
        logger.error(f'error executing query {request.query}: {e}')
        logger.error(traceback.format_exc())
        raise e

if __name__ == '__main__':

    from art import text2art
    print(text2art('PondSQL', font='broadway'))

    logger.info(f"starting pondsql on port {_global_pondsql_port}")
    logger.info(f"using mongodb connection string {_global_schema_mongodb_connection_string}")
    logger.info(f"using mongodb database {_global_schema_mongodb_database}")
    logger.info(f"using mongodb collection {_global_schema_mongodb_collection}")
    logger.info(f"using database timeout {_global_database_timeout}")

    uvicorn.run(app, host="127.0.0.1", port=_global_pondsql_port) # ONLY listen to localhost, and use NGINX to explose to the outside world ( HTTPS Reverse Proxy)
