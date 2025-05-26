from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.future import select
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from celery.result import AsyncResult
import json

from schemas import SuccessOrErrorResponse, TextRequestModel
from config import config
from models import User
from .auth import get_current_user
from .admin.users import get_current_admin
import util.tokenizer as tokenizer
from celery_app import worker as celery_app
   
router = APIRouter()

@router.post("/get_tokens", response_model=SuccessOrErrorResponse)
async def get_tokens(text: TextRequestModel = Body(...), current_user: User = Depends(get_current_user)):
    tokens = tokenizer.get_tokens(text.text)
    return SuccessOrErrorResponse(success=True, data=tokens)


@router.get("/celery_task_status/{task_id}")
async def task_progress(task_id: str, current_user: User = Depends(get_current_admin)):
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        # 序列化 task_result
        task_data = {
            "task_id": task_id,
            "status": task_result.state,
            "info": task_result.info,  # 进度信息
            "result": task_result.result,  # 最终结果
            "started": task_result.started,  # 任务开始时间
            "succeeded": task_result.successful(),  # 任务是否成功
            "failed": task_result.failed(),  # 任务是否失败
        }
        # 将 task_result 的数据转换为 JSON
        return json.dumps(task_data, default=str)  # 使用 default=str 来处理日期等非序列化类型
    except Exception as e:
        # 捕获任何错误并返回适当的 HTTP 错误响应
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    