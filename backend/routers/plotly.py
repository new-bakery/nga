from fastapi import APIRouter, Depends, HTTPException, status, Body, Response
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
import s3_api
from s3_api import BotoCoreError, NoCredentialsError, EndpointConnectionError, ClientError

   
router = APIRouter()

@router.get("/view/{object_name}")
async def view(object_name: str, current_user: User = Depends(get_current_user)):
    try:
        current_user_id = current_user.id
        object_name = f"plotly/{current_user_id}/{object_name}"
        result = s3_api.download_fileobj(object_name, "text/html")
        file_obj = result["file_obj"]
        media_type = result["media_type"]
        filename_safe = result["filename_safe"]
        return Response(content=file_obj.getvalue(), media_type = media_type,
                         headers={"Content-Disposition": f"inline; filename={filename_safe}"})
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

