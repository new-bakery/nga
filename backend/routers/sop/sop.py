from fastapi import APIRouter, Depends, HTTPException, status, Body, File, UploadFile, Form, Request
from fastapi.responses import Response
import logging
from typing import List, Optional
from bson import ObjectId

from database import get_pgdb, get_mgdb, AsyncSession
from models import User
from ..auth import get_current_user
from schemas import SuccessOrErrorResponse
from schemas.sop import *
from config import config
from util.json_encoder import copy_without_control_keys
from .sop_embedding import *

logger = logging.getLogger()

router = APIRouter()


@router.get("", response_model=List[SOP_ListItem])
async def get_sops(search_condition: Optional[str] = "", page_size: int = 10, page_num: int = 1, current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    
    skip = (page_num - 1) * page_size
    limit = page_size
    sops = mgdb.get_collection(config.SOP_COLLECTION_NAME)
    
    if search_condition and len(str.strip(search_condition)) > 0:
        results = await sops.find({
            "$text": {
                "$search": search_condition
            }
        }).to_list(None)  # 返回结果列表
    else:
        results = await sops.find({}).skip(skip).limit(limit).to_list(None)
    
    results = [{**result, "id": str(result["_id"])} for result in results]        
    sop_list = [SOP_ListItem.model_validate(result) for result in results]
    return sop_list


@router.get("/{sop_doc_id}", response_model=SOP)
async def get_sop(sop_doc_id: str, current_user: User = Depends(get_current_user), mgdb = Depends(get_mgdb)):
    sop_collection = mgdb[config.SOP_COLLECTION_NAME]
    doc = await sop_collection.find_one({"_id": ObjectId(sop_doc_id)})
    if doc:
        sop = SOP.model_validate({**doc, "id": str(doc["_id"])})
        return sop
    else:
        raise HTTPException(status_code=404, detail=f"SOP {sop_doc_id} not found")


@router.post("", response_model=SuccessOrErrorResponse)
async def create_sop(sop: SOP, current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    sop_collection = mgdb[config.SOP_COLLECTION_NAME]
    result = await sop_collection.insert_one(sop.model_dump())
    doc_id = str(result.inserted_id)
    doc = await sop_collection.find_one({"_id": ObjectId(doc_id)})
    if doc:
        sop = SOP.model_validate({**doc, "id": str(doc["_id"])})
        embedding_sops([sop])
    return SuccessOrErrorResponse(success=True, data=doc_id)


@router.put("/{sop_doc_id}", response_model=SuccessOrErrorResponse)
async def update_sop(sop_doc_id: str, sop: SOP, current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    sop_collection = mgdb[config.SOP_COLLECTION_NAME]
    result = await sop_collection.update_one({"_id": ObjectId(sop_doc_id)}, {"$set": sop.model_dump()})
    if result.matched_count == 0:
        raise Exception("Failed to update target document")
    doc = await sop_collection.find_one({"_id": ObjectId(sop_doc_id)})
    if doc:
        sop = SOP.model_validate({**doc, "id": str(doc["_id"])})
        embedding_sops([sop])
    return SuccessOrErrorResponse(success=True, data=sop_doc_id)


@router.delete("/{sop_doc_id}")
async def get_sop(sop_doc_id: str, current_user: User = Depends(get_current_user), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    sop_collection = mgdb[config.SOP_COLLECTION_NAME]
    sop_collection.delete_one({"_id": ObjectId(sop_doc_id)})
    remove_redis(sop_doc_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    
