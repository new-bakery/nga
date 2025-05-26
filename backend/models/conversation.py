from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
import datetime
from sqlalchemy.ext.mutable import MutableList

from pydantic import validator
import bson

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    doc_id = Column(String, nullable=False)
    source_ids = Column(MutableList.as_mutable(JSON), nullable=True) # List of source ids, 必须要在pg里面定义。因为source的情况会发生变化，而变化在pg里发生。
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 确保非空
    created_at = Column(DateTime, default=datetime.datetime.now().replace(tzinfo=None))  # 统一时间格式,注意，是App服务器本地时间
    
    user = relationship("User", back_populates="conversations")
    
    @validator('doc_id')
    def validate_objectid(cls, v):
        if len(v) != 24 or not bson.ObjectId.is_valid(v):
            raise ValueError('Invalid ObjectId format')
        return v
    