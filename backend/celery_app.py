# celery_app.py
from celery import Celery, shared_task

from config import config
from logging_config import setup_logging




setup_logging()

# 配置 Celery 使用 Redis 作为消息代理
worker = Celery('worker', broker=config.CELERY_REDIS_CONNECTION_STRING)


# 可选：设置时区
worker.conf.timezone = config.CELERY_TIMEZONE

# 设置 Celery 任务结果存储
worker.conf.result_backend = config.CELERY_REDIS_CONNECTION_STRING



from source_types._detect_relationships import task_detect_relationships
from source_types._embedding import task_embedding
from source_types._statistics import task_statistics

from source_types.sqlserver import task_calculate_signature
from source_types.tabularfile import task_calculate_signature


# # @worker.task(bind=True, name = "source_types.sqlserver.task_statistics")
# @shared_task(name="task_statistics")
# def task_statistics(source_id: int):
#     print("Hahaha!")
#     print(f'Task started for source {source_id}')

# celery -A celery_app.worker worker --loglevel=info 