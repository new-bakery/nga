import boto3
import uuid
import io
import os
import datetime
from botocore.exceptions import BotoCoreError, NoCredentialsError, EndpointConnectionError, ClientError
from urllib.parse import quote

from models.user import User
from config import config


s3_client = boto3.client('s3',
                        endpoint_url = config.S3_ENDPOINT,
                        aws_access_key_id = config.S3_ACCESS_KEY,
                        aws_secret_access_key = config.S3_SECRET_KEY,
                        region_name = config.S3_REGION_NAME,
                        use_ssl = config.S3_Use_SSL,
                        verify = config.S3_VERIFY) 


def upload_fileobj(category: str, filename: str, file_obj: io.BytesIO, current_user: User, media_type: str = None) -> dict:
    if not media_type:
        media_type = "application/octet-stream"
    base_name, ext = os.path.splitext(filename)
    unique_id = uuid.uuid4().hex  # 生成 UUID
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    # s3_object_name = f"{category}/{str(current_user.id)}/{base_name}_{timestamp}{ext}"
    s3_object_name = f"{category}/{str(current_user.id)}/{unique_id}_{timestamp}"
    s3_client.upload_fileobj(file_obj, config.S3_BUCKET_NAME, s3_object_name, 
                                ExtraArgs={"ContentType": media_type,
                                        "Metadata" : { "original_filename": filename}} )
    return {"object_name": s3_object_name, "media_type": media_type, "original_filename": filename}


def download_fileobj(object_name: str, media_type: str = None) -> dict:
    if not media_type:
        media_type = "application/octet-stream"
    file_obj = io.BytesIO()
    s3_client.download_fileobj(config.S3_BUCKET_NAME, object_name, file_obj)
    file_obj.seek(0)
    response = s3_client.head_object(Bucket=config.S3_BUCKET_NAME, Key=object_name)
    media_type = response.get("ContentType", media_type)
    metadata = response.get("Metadata", {})
    original_filename = metadata.get("original_filename", object_name)
    filename_safe = quote(original_filename)
    return {"file_obj": file_obj, "media_type": media_type, "filename_safe": filename_safe}


def check_exists(object_name: str) -> bool:
    try:
        s3_client.head_object(Bucket=config.S3_BUCKET_NAME, Key=object_name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            raise
