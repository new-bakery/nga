from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from typing import List
from sqlalchemy import func
from sqlalchemy.future import select
from bson import ObjectId

from database import get_pgdb, get_mgdb, AsyncSession
from models import Source, User
from .users import get_current_admin
from schemas.source import SourceResponse, SourceDetailResponse
from config import config
from util.json_encoder import copy_without_control_keys

router = APIRouter()

@router.get("", response_model=List[SourceResponse])
async def get_sources(current_admin: User = Depends(get_current_admin), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    result = await pgdb.execute(select(Source))
    sources = [SourceResponse.model_validate(source) for source in result.scalars().all()]
    
    if len(sources) > 0:
        schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
        projection = {
            "_id": 0,
            "source_name": 1,
            "connection": 1,
            "description": 1,
        }
        for source in sources:
           doc = await schema_collection.find_one({"_id": ObjectId(source.doc_id)}, projection=projection)
           if doc:
               source.source_name = doc.get("source_name","")
               source.connection = doc.get("connection",{})
               source.description = doc.get("description",[])
    return sources
    


@router.get("/{source_id}", response_model=SourceDetailResponse)
async def get_source(source_id: int, current_admin: User = Depends(get_current_admin), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    result = await pgdb.execute(select(Source).filter(Source.id == source_id))
    db_source = result.scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    detail = SourceDetailResponse.model_validate(db_source)
    schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
    projection = {
            "tables": 0,
    }
    doc = await schema_collection.find_one({"_id": ObjectId(detail.doc_id)}, projection=projection)
    if doc:
        doc = copy_without_control_keys(doc)
        detail.source_name = doc.get("source_name","")
        detail.connection = doc.get("connection",{})
        detail.description = doc.get("description",[])
        detail.doc = doc
    return detail


@router.put("/mark_is_private/{source_id}", response_model=SourceDetailResponse)
async def mark_is_private(source_id: int, is_private: bool, current_admin: User = Depends(get_current_admin), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    result = await pgdb.execute(select(Source).filter(Source.id == source_id))
    db_source = result.scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    if db_source.is_private != is_private:
        db_source.is_private = is_private
        await pgdb.commit()
        await pgdb.refresh(db_source)
    
    detail = SourceDetailResponse.model_validate(db_source)
    schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
    projection = {
            "tables": 0,
    }
    doc = await schema_collection.find_one({"_id": ObjectId(detail.doc_id)}, projection=projection)
    if doc:
        doc = copy_without_control_keys(doc)
        detail.source_name = doc.get("source_name","")
        detail.connection = doc.get("connection",{})
        detail.description = doc.get("description",[])
        detail.doc = doc
    return detail


@router.delete("/{source_id}")
async def delete_source(source_id: int, current_admin: User = Depends(get_current_admin), pgdb: AsyncSession = Depends(get_pgdb), mgdb = Depends(get_mgdb)):
    result = await pgdb.execute(select(Source).filter(Source.id == source_id))
    db_source = result.scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    await pgdb.delete(db_source)
    await pgdb.commit()
    schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
    await schema_collection.delete_one({"_id": ObjectId(db_source.doc_id)})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
