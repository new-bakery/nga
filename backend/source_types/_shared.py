import json
import logging
import time
from sqlalchemy.future import select
import redis
from redis.exceptions import LockError
import asyncio

from database import get_pgdb, get_mgdb
from models import Source
from config import config


logger = logging.getLogger()

async def update_source_status(source_id : int, status: dict):
    LOCK_NAME = f"source_status_lock:{source_id}"
    redis_client = redis.StrictRedis.from_url(config.REDIS_CONNECTION_STRING, decode_responses=False)
    retries = 0
    max_retries = 10  # 最大重试次数
    db_source = None
    while retries < max_retries:
        logger.info(f'{retries} / {max_retries} trying to lock {LOCK_NAME}')
        if redis_client.setnx(LOCK_NAME, 1):  # 如果获取到锁
            try:
                logger.info('update status')
                async for pgdb in get_pgdb():
                    result = await pgdb.execute(select(Source).filter( (Source.id == source_id) ))
                    db_source = result.scalar_one_or_none()
                    if not db_source:
                        logger.error("source not found")
                        raise Exception("source not found")
                    logger.info(f'current source status: {db_source.status}')
                    db_source.status.update(status)
                    logger.info(f'updated source status: {db_source.status}')
                    pgdb.add(db_source)
                    await pgdb.commit()
                    await pgdb.flush()
                    await pgdb.refresh(db_source)
                    logger.info('source status updated')
                break
            finally:
                redis_client.delete(LOCK_NAME)
                logger.info('lock released')
        else:
            logger.info('waiting for lock, retrying...')
            retries += 1
            # time.sleep(0.1)  # 等待再试
            await asyncio.sleep(0.5)

    if retries == max_retries:
        logger.error('Failed to acquire lock after maximum retries')
        # 如果超过最大重试次数，可以选择记录错误或者抛出异常
        raise LockError("Unable to acquire lock after multiple attempts.")
    else:
        return db_source

