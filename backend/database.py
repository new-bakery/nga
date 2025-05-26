from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

from config import config

Base = declarative_base()

async_engine = create_async_engine(config.POSTGRESQL_CONNECTION_STRING, echo = config.DB_ECHO)
AsyncSessionLocal = sessionmaker(bind = async_engine, class_= AsyncSession, expire_on_commit = False)

motor_client = AsyncIOMotorClient(config.MONGODB_CONNECTION_STRING)  # 从配置中获取MongoDB连接URL
mongodb_db = motor_client.get_database(config.MONGODB_DATABASE_NAME)  # 获取MongoDB数据库对象


async def startup(app):
    app.motor_client = motor_client
    app.mongodb_db = mongodb_db
    await init_mongodb(mongodb_db)
    
async def shutdown(app):
    if app.motor_client:
        motor_client.close()


#Dependency
async def get_pgdb():
    async with AsyncSessionLocal() as db:
        try:
            yield db  # 提供异步数据库会话
        finally:
            # 在这里确保会话被关闭
            await db.close()

# Dependency for Motor
async def get_mgdb():
    try:
        yield mongodb_db  # 返回数据库连接
    finally:
        pass


async def init_mongodb(mgdb):
    
    collection_names = [config.SCHEMA_COLLECTION_NAME, config.SOP_COLLECTION_NAME, config.CONVERSATION_COLLECTION_NAME]
    
    existing_collection_names = await mgdb.list_collection_names()
    
    for collection_name in collection_names:
        if collection_name not in existing_collection_names:
            await mgdb.create_collection(collection_name)
    
    sops = mgdb[config.SOP_COLLECTION_NAME]
    
    existing_sops_indexes = await sops.index_information()
    
    index_fields = ["title", "description", "tags", "domains", "steps.title", "steps.description", "steps.action", "steps.examples", 
                "analysis_guidelines.title", "analysis_guidelines.condition" , "analysis_guidelines.action" ,"analysis_guidelines.data_sources" ]

    if config.SOP_SEARCH_INDEX_NAME not in existing_sops_indexes:
        await sops.create_index([ (field, "text") for field in index_fields] , name=config.SOP_SEARCH_INDEX_NAME)
    else:
        existing_index_fields = list(existing_sops_indexes[config.SOP_SEARCH_INDEX_NAME]['weights'].keys())
        if set(existing_index_fields) != set(index_fields):
             await sops.drop_index(config.SOP_SEARCH_INDEX_NAME)
             await sops.create_index([ (field, "text") for field in index_fields] , name=config.SOP_SEARCH_INDEX_NAME)
             await sops.reindex()
             
            
        
    