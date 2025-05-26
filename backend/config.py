from dotenv import load_dotenv
import os
import json
from typing import List

# Load environment variables
load_dotenv()

class SystemConfig:
    
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # CORS Settings
    CORS_ORIGINS: List[str] = json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:5173", "http://localhost:3000"]'))
    
    # Postgresql Database
    POSTGRESQL_CONNECTION_STRING: str = os.getenv("POSTGRESQL_CONNECTION_STRING")
    
    # MongoDB Database
    MONGODB_CONNECTION_STRING: str = os.getenv("MONGODB_CONNECTION_STRING")
    
    # MongoDB Database and Collection
    MONGODB_DATABASE_NAME: str = os.getenv("MONGODB_DATABASE_NAME")
    SCHEMA_COLLECTION_NAME: str = os.getenv("SCHEMA_COLLECTION_NAME")
    CONVERSATION_COLLECTION_NAME: str = os.getenv("CONVERSATION_COLLECTION_NAME")
    SOP_COLLECTION_NAME : str = os.getenv("SOP_COLLECTION_NAME")
    SOP_SEARCH_INDEX_NAME: str = os.getenv("SOP_SEARCH_INDEX_NAME")
    
    # Redis
    REDIS_CONNECTION_STRING: str = os.getenv("REDIS_CONNECTION_STRING")
    REDIS_SCHEMA_INDEX_NAME: str = os.getenv("REDIS_SCHEMA_INDEX_NAME")
    REDIS_CONVERSATION_INDEX_NAME: str = os.getenv("REDIS_CONVERSATION_INDEX_NAME")
    REDIS_SOP_INDEX_NAME: str = os.getenv("REDIS_SOP_INDEX_NAME")
    
    # S3
    S3_ENDPOINT: str = os.getenv("S3_ENDPOINT")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME")
    S3_Use_SSL: str = os.getenv("S3_Use_SSL").lower() == "true"
    S3_REGION_NAME: str = os.getenv("S3_REGION_NAME")
    S3_VERIFY: str | bool = False if os.getenv("S3_VERIFY").lower() == "false" else os.getenv("S3_VERIFY")
    
    # PondSQL
    PONDSQL_CONNECTION_STRING: str = os.getenv("PONDSQL_CONNECTION_STRING")
    
    DB_ECHO = os.getenv("DB_ECHO", "False").lower() == "true"
    DB_LANG = os.getenv("DB_LANG", "en")
    SIGNATURE_THRESHOLD = float(os.getenv("SIGNATURE_THRESHOLD", "0.8"))
    NAME_TYPE_THRESHOLD = float(os.getenv("NAME_TYPE_THRESHOLD", "0.6"))
    MAX_ROWS_TO_SIGNATURE = int(os.getenv("MAX_ROWS_TO_SIGNATURE", "10000"))
    SCHEMA_TOKEN_THRESHOLD = int(os.getenv("SCHEMA_TOKEN_THRESHOLD", "10000"))
    SMILARITY_THRESHOLD = float(os.getenv("SMILARITY_THRESHOLD", "0.5"))
    LLM_CONTEXT_SIZE = int(os.getenv("LLM_CONTEXT_SIZE", "128"))
    
    DIFY_ACCOUNT_USER_EMAIL = os.getenv("DIFY_ACCOUNT_USER_EMAIL")
    DIFY_ACCOUNT_USER_PASSWORD = os.getenv("DIFY_ACCOUNT_USER_PASSWORD")
    DIFY_WORKFLOW_ENDPOINT = os.getenv("DIFY_WORKFLOW_ENDPOINT")
    
    DIFY_TABLE_ANNOTATION_APP_KEY = os.getenv("DIFY_TABLE_ANNOTATION_APP_KEY")
    ANNOTATION_LANGUAGES = os.getenv("ANNOTATION_LANGUAGES")
    
    DIFY_EMBEDDING_APP_KEY = os.getenv("DIFY_EMBEDDING_APP_KEY")
    DIFY_SQL_AGENT_APP_KEY = os.getenv("DIFY_SQL_AGENT_APP_KEY")
    DIFY_TOPIC_GENERATOR_APP_KEY = os.getenv("DIFY_TOPIC_GENERATOR_APP_KEY")
    DIFY_PLANNER_APP_KEY = os.getenv("DIFY_PLANNER_APP_KEY")
    DIFY_PLANNER2_APP_KEY = os.getenv("DIFY_PLANNER2_APP_KEY")
    DIFY_CHAT_AGENT_APP_KEY = os.getenv("DIFY_CHAT_AGENT_APP_KEY")
    DIFY_PYTHON_DATA_AGENT_APP_KEY = os.getenv("DIFY_PYTHON_DATA_AGENT_APP_KEY")
    DIFY_PLOTLY_AGENT_APP_KEY = os.getenv("DIFY_PLOTLY_AGENT_APP_KEY")

    CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE")
    
    TOKENIZER = os.getenv("TOKENIZER")
    MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR")
    
    CELERY_REDIS_CONNECTION_STRING = os.getenv("CELERY_REDIS_CONNECTION_STRING")

# Create a singleton instance
config = SystemConfig() 